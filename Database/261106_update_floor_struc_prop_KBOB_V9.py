"""
Abgleich der Tabelle floor_struc_prop mit der KBOB-Liste 2022, Version 9.0.

Ausgangslage: database_261009.db (Database/ und Workflow/ enthalten dieselbe Datei).
Ergebnis:     database_261106.db mit korrigierten Werten, neuer Zeitstempel.

Vorgehen: Die zehn nichttragenden Materialien von floor_struc_prop werden ueber
die KBOB ID-Nr. in der Liste V9.0 gesucht und ihr GWP-Wert (Spalte
"Treibhausgasemissionen Total", Herstellung + Entsorgung, in kg CO2-eq/kg bzw.
pro Bezugseinheit) mit dem Wert in der Datenbank verglichen. Abweichende Werte
werden in der neuen Datenbank ueberschrieben, uebrige Tabellen bleiben
unveraendert.

Hinweis: Die Datenbank wird sonst ueber Convert_Excel_to_DB.py aus
260811_Datenbankdefinition.xlsx erzeugt. Dieses Excel ist formelgesteuert und
wird hier nicht veraendert. Die dortige Zelle floor_struc_prop!H5
("Kies gebrochen") enthaelt weiterhin 0.018 und ist vor der naechsten
Konvertierung von Hand auf 0.0176 zu setzen, sonst geht die Korrektur verloren.
"""

import os
import shutil
import sqlite3
import tempfile

import openpyxl

# Die KBOB-Liste liegt ausserhalb des Repos. Der erste existierende Pfad wird
# verwendet; bei Bedarf eigenen Pfad zuoberst eintragen.
KBOB_XLSX_CANDIDATES = [
    "Ökobilanzdaten_im_Baubereich_V9.0.xlsx",
    os.path.expanduser(
        "~/Documents/04 Working Folder/ETH Nachhaltigkeit im Bau/"
        "21_Analyse typischer Tragwerke/01_Daten und Pläne/"
        "Ökobilanzdaten_im_Baubereich_V9.0.xlsx"),
    os.path.expanduser(
        "~/mnt/21_Analyse typischer Tragwerke/01_Daten und Pläne/"
        "Ökobilanzdaten_im_Baubereich_V9.0.xlsx"),
]


def find_kbob_file():
    for path in KBOB_XLSX_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "KBOB-Liste V9.0 nicht gefunden, geprueft:\n  " + "\n  ".join(KBOB_XLSX_CANDIDATES))


KBOB_SHEET = "Baumaterialien Matériaux"
COL_ID, COL_NAME, COL_DENS, COL_REF, COL_GWP = 0, 2, 5, 6, 25  # 0-basiert

SRC_DB = "database_261009.db"
DST_DB = "database_261106.db"


def read_kbob(path):
    """liefert {ID-Nummer: (Name, Rohdichte, Bezug, GWP total)} der KBOB-Liste"""
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheet = workbook[KBOB_SHEET]
    data = {}
    for row in sheet.iter_rows(values_only=True):
        key = row[COL_ID]
        if key is None:
            continue
        key = str(key).strip()
        if not key or not key[0].isdigit() or "." not in key:
            continue
        data[key] = (row[COL_NAME], row[COL_DENS], row[COL_REF], row[COL_GWP])
    workbook.close()
    return data


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    kbob_file = find_kbob_file()
    print(f"KBOB-Liste: {kbob_file}")
    kbob = read_kbob(kbob_file)

    # Die Datenbank wird in einem temporaeren Verzeichnis bearbeitet und erst am
    # Schluss an den Zielort kopiert: auf eingebundenen Netz- oder Cloud-Laufwerken
    # schlaegt das Sperren der SQLite-Datei sonst mit "disk I/O error" fehl.
    work_dir = tempfile.mkdtemp()
    work_db = os.path.join(work_dir, os.path.basename(DST_DB))
    shutil.copyfile(SRC_DB, work_db)
    connection = sqlite3.connect(work_db)
    cursor = connection.cursor()

    rows = cursor.execute(
        'SELECT "mat_ID [Integer]", "KBOB ID-Nr.", "name[string]", "GWP [float, kg/kg]" '
        'FROM floor_struc_prop WHERE "KBOB ID-Nr." IS NOT NULL'
    ).fetchall()

    changed = []
    for mat_id, kbob_id, name, gwp_db in rows:
        entry = kbob.get(str(kbob_id).strip())
        if entry is None:
            print(f"{mat_id} {kbob_id} {name}: in V9.0 nicht gefunden, unveraendert")
            continue
        gwp_v9 = to_float(entry[3])
        if gwp_v9 is None:
            print(f"{mat_id} {kbob_id} {name}: kein GWP-Wert in V9.0, unveraendert")
            continue
        # Parkett hat den Bezug m2, die Datenbank rechnet mit einer fiktiven
        # Rohdichte: GWP[kg/kg] = GWP[kg/m2] / h / Rohdichte[kg/m2]
        if str(entry[2]).strip().lower() == "m2":
            h_fix, dens = cursor.execute(
                'SELECT "h_fix [float, m]", "density [float, kg/m^3]" '
                'FROM floor_struc_prop WHERE "mat_ID [Integer]" = ?', (mat_id,)
            ).fetchone()
            gwp_v9 = gwp_v9 / (float(h_fix) * float(dens))
        if abs(float(gwp_db) - gwp_v9) < 1e-9:
            continue
        cursor.execute(
            'UPDATE floor_struc_prop SET "GWP [float, kg/kg]" = ?, "GWP [kg CO2 eq /t]" = ? '
            'WHERE "mat_ID [Integer]" = ?', (gwp_v9, gwp_v9 * 1e3, mat_id)
        )
        changed.append((mat_id, name, float(gwp_db), gwp_v9))

    connection.commit()
    connection.close()
    shutil.copyfile(work_db, DST_DB)
    shutil.rmtree(work_dir, ignore_errors=True)

    if changed:
        print(f"Geaenderte Werte in {DST_DB}:")
        for mat_id, name, old, new in changed:
            print(f"  {mat_id} {name}: {old} -> {new} kg CO2-eq/kg")
    else:
        print(f"Keine Abweichungen gefunden, {DST_DB} entspricht {SRC_DB}")


if __name__ == "__main__":
    main()
