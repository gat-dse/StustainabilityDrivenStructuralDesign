import pandas as pd
import sqlite3
import numpy as np

# 1. Daten aus der SQLite-Datenbank laden
conn = sqlite3.connect("database_260805.db")
df_db = pd.read_sql_query("SELECT * FROM products", conn)
conn.close()

# 2. Daten direkt aus der Excel-Datei laden (echte Header in Zeile 3 -> Index 2)
excel_file = "260805_Datenbankdefinition.xlsx"
df_excel = pd.read_excel(excel_file, sheet_name="products", engine="openpyxl")

# Spaltennamen trimmen (Leerzeichen am Anfang/Ende entfernen)
df_db.columns = df_db.columns.str.strip()
df_excel.columns = df_excel.columns.str.strip()

# 3. Radikale Bereinigung und Rundung aller Spalten
for df in [df_db, df_excel]:
    for col in df.columns:
        # Versuchen, die Spalte in Zahlen umzuwandeln und auf 4 Nachkommastellen zu runden
        numeric_col = pd.to_numeric(df[col], errors='coerce')

        if numeric_col.notna().any():
            # Wenn die Spalte Zahlen enthält, runden wir sie und füllen NaNs mit leerem Text
            df[col] = numeric_col.round(5).fillna("").astype(str)
        else:
            # Reine Textspalten normal bereinigen
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["N/A", "NaN", "-", "None", "nan", "<NA>"], "")

# 4. Schlüssel-Spalten festlegen (Exakter Name aus der jeweiligen Quelle)
id_col_db = "PRO_ID"      # Name in der SQLite-Datenbank
id_col_excel = "PRO_ID"  # Name in deiner Excel-Datei

# Spalten als Index setzen
df_db_indexed = df_db.set_index(id_col_db)
df_excel_indexed = df_excel.set_index(id_col_excel)

# 5. Überprüfen, ob IDs komplett fehlen oder zu viel sind
ids_in_db_only = df_db_indexed.index.difference(df_excel_indexed.index)
ids_in_excel_only = df_excel_indexed.index.difference(df_db_indexed.index)

print(f"\n--- Struktur-Abgleich ---")
print(f"Zeilen in DB: {len(df_db)} | Zeilen in Excel: {len(df_excel)}")
if len(ids_in_db_only) > 0:
    print(f"⚠️ {len(ids_in_db_only)} IDs sind NUR in der DB: {list(ids_in_db_only)[:10]}...")
if len(ids_in_excel_only) > 0:
    print(f"⚠️ {len(ids_in_excel_only)} IDs sind NUR in Excel: {list(ids_in_excel_only)[:10]}...")

# 6. Inhaltlicher Vergleich der gemeinsamen Zeilen und Spalten
common_ids = df_db_indexed.index.intersection(df_excel_indexed.index)
common_cols = [col for col in df_excel_indexed.columns if col in df_db_indexed.columns]

df_db_compare = df_db_indexed.loc[common_ids, common_cols]
df_excel_compare = df_excel_indexed.loc[common_ids, common_cols]

import math

print("\n--- Inhalts-Abgleich (Detailprüfung) ---")
if df_db_compare.equals(df_excel_compare):
    print("🎉 Perfekt! Alle gemeinsamen Zeilen sind inhaltlich absolut identisch.")
else:
    print("Suche nach echten Unterschieden mit numerischer Toleranz...")

    true_diff_found = False

    for current_id in common_ids:
        for col in common_cols:
            val_db = df_db_compare.loc[current_id, col]
            val_excel = df_excel_compare.loc[current_id, col]

            # 1. Beide Werte bereinigen
            clean_db = str(val_db).strip()
            clean_excel = str(val_excel).strip()

            # 2. Leere Felder ignorieren
            if clean_db in ["nan", ""] and clean_excel in ["nan", ""]:
                continue

            # 3. Versuchen, als Zahlen mit Toleranz zu vergleichen
            try:
                num_db = float(clean_db)
                num_excel = float(clean_excel)
                # Erlaubt eine minimale Abweichung (z.B. 0.0001)
                if math.isclose(num_db, num_excel, abs_tol=1e-4):
                    continue
            except ValueError:
                # Wenn es Text ist (z.B. Produktname), normal vergleichen
                if clean_db == clean_excel:
                    continue

            # Wenn wir hier landen, ist es ein echter Unterschied!
            print(f"\n💡 Echter Unterschied gefunden bei PRO_ID: {current_id}")
            text_id_db = df_db_indexed.loc[current_id, 'ID'] if 'ID' in df_db_indexed.columns else "Unbekannt"
            print(f"Zugehörige ID (Spalte A): {text_id_db}")
            print(f"Spalte '{col}':")
            print(f"  -> In DB   : '{val_db}'")
            print(f"  -> In Excel: '{val_excel}'")
            print("-" * 30)
            true_diff_found = True
            break

        if true_diff_found:
            break

    if not true_diff_found:
        print("🎉 Keine echten Unterschiede mehr! Alle Abweichungen lagen im Bereich von Rundungsfehlern.")