# -*- coding: utf-8 -*-
"""
Erzeugt das Analyse-Excel der Bestandesbauten (Wohnbauten).

Eingang:
  bestand_daten.py                  Objekte, Spannweiten, Quellen (von Hand gepflegt)
  251204_Auswertung.xlsx            Schichtaufbauten der Decken (nur gelesen, nie veraendert)
  Oekobilanzdaten_im_Baubereich_V9.0.xlsx   KBOB-Kennwerte der nichttragenden Schichten

Ausgang:
  <Zeitstempel>_Bestandesanalyse_Wohnbauten.xlsx

Rechenweg:
  tragende Schichten    Dicke x Rohdichte x GWP, zwei Varianten (EPD heute / KBOB)
  Bewehrung             Volumenanteil x 7850 kg/m3 x GWP, zwei Varianten
  Bodenaufbau           Dicke x Rohdichte x GWP nach KBOB V9.0, bzw. direkt pro m2 bei Bezug m2
  Bezugsgroesse         1 m2 Deckenflaeche, Herstellung + Entsorgung, ohne Transport, ohne Amortisation
"""

import os
import sys
from datetime import date

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bestand_daten as D

# ----------------------------------------------------------------------------------------------------------------------
# Pfade: erster existierender Eintrag wird verwendet
ANALYSE_ORDNER_KANDIDATEN = [
    os.path.expanduser("~/Documents/04 Working Folder/ETH Nachhaltigkeit im Bau/"
                       "21_Analyse typischer Tragwerke/01_Daten und Pläne"),
    os.path.expanduser("~/mnt/21_Analyse typischer Tragwerke/01_Daten und Pläne"),
]
AUSWERTUNG_XLSX = "251204_Auswertung.xlsx"
KBOB_XLSX = "Ökobilanzdaten_im_Baubereich_V9.0.xlsx"
KBOB_SHEET = "Baumaterialien Matériaux"


def analyse_ordner():
    for p in ANALYSE_ORDNER_KANDIDATEN:
        if os.path.isdir(p):
            return p
    raise FileNotFoundError("Ordner '01_Daten und Pläne' nicht gefunden, geprueft:\n  "
                            + "\n  ".join(ANALYSE_ORDNER_KANDIDATEN))


# ----------------------------------------------------------------------------------------------------------------------
def lies_kbob(pfad):
    """{Materialname: dict} der KBOB-Liste V9.0"""
    wb = openpyxl.load_workbook(pfad, data_only=True, read_only=True)
    ws = wb[KBOB_SHEET]
    daten = {}
    for row in ws.iter_rows(values_only=True):
        kid, name, dichte, bezug, gwp = row[0], row[2], row[5], row[6], row[25]
        if kid is None or name is None:
            continue
        kid = str(kid).strip()
        if not kid or not kid[0].isdigit() or "." not in kid:
            continue
        daten[str(name).strip()] = dict(id=kid, name=str(name).strip(), dichte=dichte, bezug=bezug, gwp=gwp)
    wb.close()
    return daten


def lies_aufbauten(pfad):
    """Schichtaufbauten aus 251204_Auswertung.xlsx, Blatt Bodenaufbauten"""
    wb = openpyxl.load_workbook(pfad, data_only=True, read_only=True)
    ws = wb["Bodenaufbauten"]
    zeilen = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        objekt = row[0]
        if objekt is None or str(objekt).strip() in ("", "Objekt", "TEST", "Kopieren"):
            continue
        if not row[5] and not row[6]:
            continue  # leere Platzhalterzeile im Quell-Excel
        zeilen.append(dict(objekt=str(objekt).strip(), nr=row[1], funktion=row[2], material=row[3],
                           gruppe=row[4], kbob_name=row[5], dicke_mm=row[6], anteil=row[7],
                           bezug=row[8], rohdichte=row[9]))
    wb.close()
    return zeilen


def zahl(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------------------------------------------------------------
def gwp_schicht(schicht, kbob, variante):
    """GWP einer Schicht [kg CO2-eq/m2].

    Tragende Baustoffe (Beton, Bewehrung, Vollholz) werden je nach Variante mit dem EPD-Mittelwert
    ("heute") oder dem KBOB-Wert ("alt") gerechnet, alle uebrigen Schichten immer mit KBOB V9.0.
    Rueckgabe: (GWP, GWP je Bezug, KBOB-Eintrag, Fehlertext)
    """
    name = str(schicht["kbob_name"]).strip() if schicht["kbob_name"] else ""
    eintrag = kbob.get(name)
    dicke = zahl(schicht["dicke_mm"], 0.0) / 1e3
    anteil = zahl(schicht["anteil"], 1.0)

    # Variante "alt": immer der KBOB-Wert V9.0 des im Aufbau genannten Materials.
    # Variante "heute": fuer Beton, Bewehrung und Vollholz der EPD-Mittelwert, sonst ebenfalls KBOB.
    stoff = D.TRAGENDE_STOFFE.get(name) if variante == "heute" else None
    if stoff is not None:
        schluessel = D.VARIANTEN[stoff][variante]
        gwp, dichte, _, _ = D.BAUSTOFFE[schluessel]
        return dicke * dichte * gwp * anteil, gwp, eintrag, None

    if eintrag is None:
        return None, None, None, f"Material '{name}' in KBOB V9.0 nicht gefunden"
    gwp = zahl(eintrag["gwp"])
    if gwp is None:
        return None, None, None, f"Material '{name}' ohne GWP-Wert in KBOB V9.0"
    if str(eintrag["bezug"]).strip().lower() == "m2":
        # Flaechenmasse: der KBOB-Wert gilt bereits pro m2 der angegebenen Schichtdicke
        return gwp * anteil, gwp, eintrag, None
    dichte = zahl(eintrag["dichte"])
    if dichte is None:
        # Rohdichte in der KBOB-Liste als Bereich angegeben: Wert aus 251204_Auswertung uebernehmen
        dichte = zahl(schicht["rohdichte"])
        if dichte is None:
            return None, gwp, eintrag, f"Material '{name}': keine eindeutige Rohdichte"
    return dicke * dichte * gwp * anteil, gwp, eintrag, None


def wende_korrekturen_an(zeilen):
    """setzt die in bestand_daten.KORREKTUREN festgehaltenen Werte und gibt die Protokollzeilen zurueck"""
    protokoll = []
    for s in zeilen:
        eintrag = D.KORREKTUREN.get((s["objekt"], s["nr"]))
        if eintrag is None:
            continue
        feld, wert, begruendung = eintrag
        protokoll.append((s["objekt"], s["nr"], feld, s[feld], wert, begruendung))
        s[feld] = wert
        s["korrigiert"] = begruendung
    return protokoll




# ----------------------------------------------------------------------------------------------------------------------
KOPF = Font(bold=True, size=10)
TITEL = Font(bold=True, size=12)
GRAU = PatternFill("solid", fgColor="DDDDDD")
GELB = PatternFill("solid", fgColor="FFF2CC")
WRAP = Alignment(wrap_text=True, vertical="top")
DUENN = Border(*[Side(style="thin", color="BFBFBF")] * 4)


def schreibe_kopf(ws, spalten, zeile=1):
    for i, (titel, breite) in enumerate(spalten, start=1):
        c = ws.cell(row=zeile, column=i, value=titel)
        c.font = KOPF
        c.fill = GRAU
        c.alignment = WRAP
        c.border = DUENN
        ws.column_dimensions[get_column_letter(i)].width = breite
    ws.freeze_panes = ws.cell(row=zeile + 1, column=1)


def main():
    ordner = analyse_ordner()
    kbob = lies_kbob(os.path.join(ordner, KBOB_XLSX))
    aufbauten = lies_aufbauten(os.path.join(ordner, AUSWERTUNG_XLSX))

    korrekturen = wende_korrekturen_an(aufbauten)

    # GWP je Objekt: tragende Schichten und Bodenaufbau getrennt, Bodenaufbau in beiden Varianten gleich
    tragend_gwp = {"heute": {}, "alt": {}}
    boden_gwp, boden_zeilen, warnungen = {}, [], []
    for s in aufbauten:
        tragend = str(s["funktion"]).strip().lower().startswith("tragend")
        werte = {}
        for variante in ("heute", "alt"):
            wert, gwp_bezug, eintrag, fehler = gwp_schicht(s, kbob, variante)
            werte[variante] = (wert, gwp_bezug, eintrag, fehler)
        wert_h, gwp_bezug_h, eintrag_h, fehler_h = werte["heute"]
        wert_a = werte["alt"][0]
        if fehler_h:
            warnungen.append(f"{s['objekt']}, Schicht {s['nr']}: {fehler_h}")
        if tragend:
            if wert_h is not None:
                tragend_gwp["heute"][s["objekt"]] = tragend_gwp["heute"].get(s["objekt"], 0.0) + wert_h
            if wert_a is not None:
                tragend_gwp["alt"][s["objekt"]] = tragend_gwp["alt"].get(s["objekt"], 0.0) + wert_a
        elif wert_h is not None:
            boden_gwp[s["objekt"]] = boden_gwp.get(s["objekt"], 0.0) + wert_h
        boden_zeilen.append((s, wert_h, wert_a, gwp_bezug_h, eintrag_h, tragend, fehler_h))

    wb = openpyxl.Workbook()

    # ---------------------------------------------------------------- Blatt 1: Objekte
    ws = wb.active
    ws.title = "Objekte"
    spalten = [("ID", 22), ("Objekt", 24), ("Portfolio", 10), ("Nutzung", 16), ("Bezugsjahr", 11),
               ("Deckentyp", 30), ("Statisches System", 30), ("Regel Spannweite", 24),
               ("lx [m]", 9), ("ly [m]", 9), ("massgebende Spannweite [m]", 14),
               ("Deckenstärke tragend [mm]", 12), ("Bewehrungsgehalt [kg/m³]", 13),
               ("GWP tragend, EPD heute [kg CO₂-eq/m²]", 15),
               ("GWP tragend, KBOB [kg CO₂-eq/m²]", 15),
               ("GWP Bodenaufbau [kg CO₂-eq/m²]", 15),
               ("GWP total, EPD heute [kg CO₂-eq/m²]", 15),
               ("GWP total, KBOB [kg CO₂-eq/m²]", 15),
               ("Data Validation", 11), ("Quelle Spannweite", 55), ("Beleg Abbildung", 20),
               ("Quelle Schichtaufbau", 45), ("Bemerkung", 70)]
    schreibe_kopf(ws, spalten)

    r = 2
    for o in D.OBJEKTE:
        gt_h = tragend_gwp["heute"].get(o["id"])
        gt_a = tragend_gwp["alt"].get(o["id"])
        gb = boden_gwp.get(o["id"])
        anteil_s = zahl(o.get("bewehrung_vol"))
        werte = [o["id"], o["objekt"], o["portfolio"], o["nutzung"], o["baujahr"], o["deckentyp"],
                 o.get("system"), o.get("regel"), o.get("lx"), o.get("ly"), o.get("l_massg"),
                 o.get("h_tragend_mm"),
                 None if anteil_s is None else round(anteil_s * 7850, 1),
                 None if gt_h is None else round(gt_h, 2),
                 None if gt_a is None else round(gt_a, 2),
                 None if gb is None else round(gb, 2),
                 None if (gt_h is None or gb is None) else round(gt_h + gb, 2),
                 None if (gt_a is None or gb is None) else round(gt_a + gb, 2),
                 o["dv"], o.get("quelle_spannweite"), o.get("beleg"), o.get("quelle_aufbau"), o.get("bemerkung")]
        for i, v in enumerate(werte, start=1):
            c = ws.cell(row=r, column=i, value=v)
            c.alignment = WRAP
            c.border = DUENN
            if o["dv"] == 0:
                c.fill = GELB
        r += 1
    ws.auto_filter.ref = f"A1:{get_column_letter(len(spalten))}{r-1}"

    # ---------------------------------------------------------------- Blatt 2: Schichtaufbauten
    ws2 = wb.create_sheet("Schichtaufbauten")
    spalten2 = [("Objekt", 22), ("Schicht Nr.", 9), ("Funktion", 13), ("Material (Textbeschrieb)", 30),
                ("KBOB-Bezeichnung", 40), ("KBOB ID-Nr.", 11), ("Schichtstärke [mm]", 11), ("Anteil [-]", 10),
                ("Bezug", 8), ("Rohdichte [kg/m³] oder Flächenmasse [kg/m²]", 16),
                ("GWP je Bezug [kg CO₂-eq]", 13), ("GWP, EPD heute [kg CO₂-eq/m²]", 13),
                ("GWP, KBOB [kg CO₂-eq/m²]", 13), ("Hinweis", 60)]
    schreibe_kopf(ws2, spalten2)
    r = 2
    for s, wert_h, wert_a, gwp_bezug, eintrag, tragend, fehler in boden_zeilen:
        hinweis = fehler or s.get("korrigiert")
        werte = [s["objekt"], s["nr"], s["funktion"], s["material"], s["kbob_name"],
                 eintrag["id"] if eintrag else None, s["dicke_mm"], s["anteil"], s["bezug"],
                 eintrag["dichte"] if eintrag else s["rohdichte"], gwp_bezug,
                 None if wert_h is None else round(wert_h, 3),
                 None if wert_a is None else round(wert_a, 3), hinweis]
        for i, v in enumerate(werte, start=1):
            c = ws2.cell(row=r, column=i, value=v)
            c.alignment = WRAP
            c.border = DUENN
            if tragend:
                c.fill = GRAU
        r += 1
    ws2.auto_filter.ref = f"A1:{get_column_letter(len(spalten2))}{r-1}"

    # ---------------------------------------------------------------- Blatt 3: Annahmen
    ws3 = wb.create_sheet("Annahmen")
    ws3.column_dimensions["A"].width = 38
    ws3.column_dimensions["B"].width = 58
    ws3.column_dimensions["C"].width = 70
    ws3["A1"] = "Annahmen und Festlegungen"
    ws3["A1"].font = TITEL
    zeilen = [
        ("", "", ""),
        ("Bezugsgrösse", "1 m² Deckenfläche", "Nur die Decke, ohne Stützen, Wände und Unterzüge"),
        ("Indikator", "Treibhausgasemissionen total",
         "Herstellung + Entsorgung, ohne Transport, ohne Amortisation. Gleiche Definition wie Total_GWP "
         "in database_261106.db und wie in 251204_Auswertung.xlsx"),
        ("Datengrundlage nichttragend", "KBOB 2022, Version 9.0",
         "Ökobilanzdaten_im_Baubereich_V9.0.xlsx, Blatt Baumaterialien"),
        ("Datengrundlage tragend", "EPD, zusätzlich KBOB als zweite Annahme",
         "Zwei Varianten je Objekt, siehe unten"),
        ("", "", ""),
        ("Beton, Annahme heute", f"{D.BAUSTOFFE['beton_epd_C30_37'][0]*1e3:.2f} kg CO₂-eq/t, "
                                 f"ρ = {D.BAUSTOFFE['beton_epd_C30_37'][1]:.0f} kg/m³",
         "Mittelwert aller 23 gültigen EPD der Klasse C30/37. Festigkeitsklasse C30/37 für alle "
         "Bestandesdecken angenommen; die tatsächliche Klasse ist in keinem Objekt dokumentiert."),
        ("Beton, Annahme alt", f"{D.BAUSTOFFE['beton_kbob'][0]*1e3:.0f} kg CO₂-eq/t, "
                               f"ρ = {D.BAUSTOFFE['beton_kbob'][1]:.0f} kg/m³",
         "KBOB Hochbaubeton (ohne Bewehrung), ID 01.002. Derselbe Wert wie in 251204_Auswertung."),
        ("Bewehrung, Annahme heute", f"{D.BAUSTOFFE['bewehrung_epd'][0]*1e3:.2f} kg CO₂-eq/t",
         "Mittelwert aller 11 gültigen EPD für B500B"),
        ("Bewehrung, Annahme alt", f"{D.BAUSTOFFE['bewehrung_kbob'][0]*1e3:.0f} kg CO₂-eq/t",
         "KBOB Armierungsstahl, ID 06.003"),
        ("Holz, Annahme heute", f"{D.BAUSTOFFE['vollholz_epd'][0]*1e3:.2f} kg CO₂-eq/t, "
                                f"ρ = {D.BAUSTOFFE['vollholz_epd'][1]:.0f} kg/m³",
         "Mittelwert aus 3 gültigen EPD für Konstruktionsvollholz"),
        ("Holz, Annahme alt", f"{D.BAUSTOFFE['vollholz_kbob'][0]*1e3:.0f} kg CO₂-eq/t, "
                              f"ρ = {D.BAUSTOFFE['vollholz_kbob'][1]:.0f} kg/m³",
         "KBOB Massivholz Fichte/Tanne/Lärche, luftgetrocknet, rau"),
        ("", "", ""),
        ("Bewehrungsgehalt", "aus 251204_Auswertung übernommen",
         "96...100 kg/m³ je nach Objekt. Ausnahme Regina Kägi Hof: dort steht 10 kg/m³, offensichtlich ein "
         "Faktor-10-Fehler; hier auf 100 kg/m³ korrigiert."),
        ("Spannweitenregel, einachsig", "Achsmass in Tragrichtung", ""),
        ("Spannweitenregel, zweiachsig", "kürzere Spannweite des massgebenden Feldes",
         "gilt für linienförmig gelagerte Felder"),
        ("Spannweitenregel, Flachdecke", "grössere Rasterachse", "gilt für punktgestützte Decken"),
        ("Decke über UG", "gesondert geführt", "siehe Blatt Decken über UG"),
        ("Bodenaufbau", "realer Aufbau je Objekt",
         "Der Bodenaufbau der Kurven des Deckenrechners (Parkett 11 mm, Unterlagsboden Zement 85 mm, "
         "Glaswolle 30 mm, zusammen 28.65 kg CO₂-eq/m²) weicht davon ab. Für den Vergleich mit den Kurven "
         "ist GWP tragend zu verwenden, GWP total ist nur innerhalb dieser Tabelle vergleichbar."),
    ]
    r = 3
    for a, b, c in zeilen:
        ws3.cell(row=r, column=1, value=a).font = KOPF
        ws3.cell(row=r, column=2, value=b).alignment = WRAP
        ws3.cell(row=r, column=3, value=c).alignment = WRAP
        r += 1

    # ---------------------------------------------------------------- Blatt 4: Decken über UG
    ws4 = wb.create_sheet("Decken über UG")
    schreibe_kopf(ws4, [("ID", 20), ("Objekt", 24), ("Deckenstärke tragend [mm]", 16), ("Quelle", 60),
                        ("Bemerkung", 60)])
    for i, d in enumerate(D.DECKEN_UEBER_UG, start=2):
        for j, v in enumerate([d["id"], d["objekt"], d["h_tragend_mm"], d["quelle"], d["bemerkung"]], start=1):
            c = ws4.cell(row=i, column=j, value=v)
            c.alignment = WRAP
            c.border = DUENN

    # ---------------------------------------------------------------- Blatt 5: Kennwerte
    ws5 = wb.create_sheet("Kennwerte Baustoffe")
    schreibe_kopf(ws5, [("Schlüssel", 22), ("Beschrieb", 48), ("GWP [kg CO₂-eq/kg]", 14),
                        ("GWP [kg CO₂-eq/t]", 14), ("Rohdichte [kg/m³]", 13), ("Quelle", 70)])
    for i, (k, (gwp, dichte, beschrieb, quelle)) in enumerate(D.BAUSTOFFE.items(), start=2):
        for j, v in enumerate([k, beschrieb, gwp, round(gwp * 1e3, 2), dichte, quelle], start=1):
            c = ws5.cell(row=i, column=j, value=v)
            c.alignment = WRAP
            c.border = DUENN

    # ---------------------------------------------------------------- Blatt 6: Offene Punkte
    ws6 = wb.create_sheet("Offene Punkte")
    schreibe_kopf(ws6, [("Objekt", 24), ("Offener Punkt", 95)])
    offen = [(o["objekt"], o["bemerkung"]) for o in D.OBJEKTE if o["dv"] < 2]
    offen += [(obj, f"Schicht {nr}, Feld {feld}: {alt} auf {neu} korrigiert. {grund}")
              for obj, nr, feld, alt, neu, grund in korrekturen]
    offen += [(a, b) for a, b in D.HINWEISE]
    offen += [("alle", w) for w in warnungen]
    for i, (a, b) in enumerate(offen, start=2):
        for j, v in enumerate([a, b], start=1):
            c = ws6.cell(row=i, column=j, value=v)
            c.alignment = WRAP
            c.border = DUENN

    name = f"{date.today():%y%m%d}_Bestandesanalyse_Wohnbauten.xlsx"
    ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    wb.save(ziel)
    print("geschrieben:", ziel)
    if warnungen:
        print("Hinweise:")
        for w in warnungen:
            print("  ", w)


if __name__ == "__main__":
    main()
