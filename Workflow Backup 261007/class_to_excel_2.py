import inspect
import pandas as pd
import os
from pathlib import Path



def class_to_excel(cls, filename, folder="Resultate"):
    """
    Exportiert eine Klassenstruktur nach Excel.
    Jede Unterklasse wird zu einem Sheet.
    Die Excel-Datei wird im angegebenen Unterordner gespeichert.
    """

    # Ordner anlegen, falls nicht vorhanden
    os.makedirs(folder, exist_ok=True)

    # Vollständiger Pfad zur Excel-Datei
    filepath = os.path.join(folder, filename)

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


def members_to_excel2(members, filename, folder="Resultate"):
    # Ordner anlegen, falls nicht vorhanden
    os.makedirs(folder, exist_ok=True)

    # Vollständiger Pfad zur Excel-Datei
    filepath = os.path.join(folder, filename)

    all_member_dataframes = []

    for i, member in enumerate(members, start=1):
        # Erstellt das DataFrame für einen Member
        df_member = member1d_to_dataframe(member)

        # Wir behalten die 'key' und 'level' Spalten nur beim ersten Member,
        # damit sie nicht in jeder Spalte wiederholt werden.
        if i == 1:
            # Umbenennen der 'value' Spalte zu 'Member_1'
            df_member = df_member.rename(columns={"value": f"Member_{i}"})
            all_member_dataframes.append(df_member)
        else:
            # Nur die 'value' Spalte extrahieren und umbenennen
            df_value_only = df_member[["value"]].rename(columns={"value": f"Member_{i}"})
            all_member_dataframes.append(df_value_only)

    if all_member_dataframes:
        # pd.concat mit axis=1 fügt die DataFrames NEBENEINANDER (Spalten) zusammen
        final_df = pd.concat(all_member_dataframes, axis=1)

        # Speichern in ein einziges Sheet
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            final_df.to_excel(writer, sheet_name="Members_Comparison", index=False)

    print(f"Excel mit Spalten-Layout erstellt:\n{filepath}")


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

import pandas as pd

def member1d_to_dataframe(member):
    rows = []

    for attr, value in vars(member).items():
        flatten(value, level=0, rows=rows, key=attr)

    return pd.DataFrame(rows)


