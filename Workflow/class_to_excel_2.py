import inspect
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

#Zeitstempel für Dateiname
def timestamped_filename(filename, timestamp=None):
    # Setzt Datum und Uhrzeit vor den Dateinamen, z.B.
    # "Members_wd_rec_simple__epd.xlsx" -> "261112_1435_Members_wd_rec_simple__epd.xlsx"
    # timestamp: optional fester Zeitstempel (datetime), damit mehrere Dateien eines Laufs denselben Präfix erhalten
    if timestamp is None:
        timestamp = datetime.now()
    return f"{timestamp:%y%m%d_%H%M}_{filename}"


def class_to_excel(cls, filename, folder="Resultate", timestamp=None):
    """
    Exportiert eine Klassenstruktur nach Excel.
    Jede Unterklasse wird zu einem Sheet.
    Die Excel-Datei wird im angegebenen Unterordner gespeichert.
    Dem Dateinamen wird Datum und Uhrzeit vorangestellt (yymmdd_HHMM_).
    """

    # Ordner anlegen, falls nicht vorhanden
    os.makedirs(folder, exist_ok=True)

    # Vollständiger Pfad zur Excel-Datei (mit Zeitstempel)
    filepath = os.path.join(folder, timestamped_filename(filename, timestamp))

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:

        for name, subcls in inspect.getmembers(cls, inspect.isclass):

            # nur Unterklassen aus demselben Modul
            if subcls.__module__ != cls.__module__:
                continue

            data = {}

            for attr, value in vars(subcls).items():
                if attr.startswith("_"):
                    continue
                if hasattr(value, "__len__"):
                    data[attr] = value

            if data:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=name, index=False)

    print(f"Excel-Datei wurde gespeichert unter:\n{filepath}")


def span_label(member):
    # Bezeichnung der Spannweite eines Members für den Sheet-Namen:
    # 1D-Systeme -> "L_6m", 2D-Systeme (lx, ly) -> "L_6x8m"
    system = member.system
    if hasattr(system, "lx") and hasattr(system, "ly"):
        return f"L_{system.lx:g}x{system.ly:g}m"
    return f"L_{system.l_tot:g}m"


def members_to_dataframe(members, names):
    # Baut das Spalten-Layout (key | level | Member_1 | Member_2 | ...) für die übergebenen Members.
    # names: Spaltennamen der Members (gleiche Länge wie members)
    all_member_dataframes = []

    for i, (member, name) in enumerate(zip(members, names)):
        # Erstellt das DataFrame für einen Member
        df_member = member1d_to_dataframe(member)

        # 'key' und 'level' nur beim ersten Member behalten, damit sie nicht in jeder Spalte wiederholt werden.
        if i == 0:
            all_member_dataframes.append(df_member.rename(columns={"value": name}))
        else:
            all_member_dataframes.append(df_member[["value"]].rename(columns={"value": name}))

    # pd.concat mit axis=1 fügt die DataFrames NEBENEINANDER (Spalten) zusammen
    return pd.concat(all_member_dataframes, axis=1)


def members_to_excel2(members, filename, folder="Resultate", timestamp=None):
    # Sheet "Members_Comparison": alle Members nebeneinander
    # zusätzlich ein Sheet pro Spannweite (z.B. "L_4m", "L_5m", ...) mit nur den Members dieser Spannweite.
    # Die Spaltennamen (Member_1, Member_2, ...) sind in allen Sheets gleich, damit man sie zuordnen kann.

    # Ordner anlegen, falls nicht vorhanden
    os.makedirs(folder, exist_ok=True)

    # Vollständiger Pfad zur Excel-Datei (mit Zeitstempel)
    filepath = os.path.join(folder, timestamped_filename(filename, timestamp))

    if not members:
        print(f"Keine Members vorhanden -> keine Excel-Datei erstellt:\n{filepath}")
        return

    names = [f"Member_{i}" for i in range(1, len(members) + 1)]

    # Members nach Spannweite gruppieren (Reihenfolge: aufsteigende Spannweite)
    groups = {}
    for member, name in zip(members, names):
        groups.setdefault(span_label(member), []).append((member, name))
    sorted_labels = sorted(groups, key=lambda lbl: [float(x) for x in lbl[2:-1].split("x")])

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        # Übersicht mit allen Members
        members_to_dataframe(members, names).to_excel(writer, sheet_name="Members_Comparison", index=False)

        # je ein Sheet pro Spannweite
        for label in sorted_labels:
            group_members = [m for m, _ in groups[label]]
            group_names = [n for _, n in groups[label]]
            df_span = members_to_dataframe(group_members, group_names)
            df_span.to_excel(writer, sheet_name=label[:31], index=False)  # Excel erlaubt max. 31 Zeichen

    print(f"Excel mit Spalten-Layout erstellt (Sheets: Members_Comparison, {', '.join(sorted_labels)}):\n{filepath}")


def flatten(obj, level=0, rows=None, key=None):
    if rows is None:
        rows = []

    SIMPLE_TYPES = (int, float, str, bool)

    # Fall 1: skalarer Wert → direkt schreiben
    if isinstance(obj, SIMPLE_TYPES):
        rows.append({
            "key": key,
            "level": level,
            "value": obj
        })

    # Fall 2: Liste / Tupel → rekursiv
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            flatten(item, level + 1, rows, key)

    # Fall 3: Objekt → Attribute rekursiv auflösen
    elif hasattr(obj, "__dict__"):
        rows.append({
            "key": key,
            "level": level,
            "value": type(obj).__name__
        })
        for attr, value in vars(obj).items():
            flatten(value, level + 1, rows, attr)

    # Fallback
    else:
        rows.append({
            "key": key,
            "level": level,
            "value": str(obj)
        })

    return rows


def member1d_to_dataframe(member):
    rows = []

    for attr, value in vars(member).items():
        flatten(value, level=0, rows=rows, key=attr)

    return pd.DataFrame(rows)


