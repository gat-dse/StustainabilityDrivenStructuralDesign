import sqlite3
import pandas as pd


def excel_to_db(excel_file, db_file):
    # 1. Excel-Datei einlesen
    # sheet_name=None lädt alle Arbeitsblätter in ein Dictionary aus DataFrames
    excel_data = pd.read_excel(excel_file, sheet_name=None)

    # 2. Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect(db_file)

    # 3. Jedes Arbeitsblatt als eigene Tabelle speichern
    for sheet_name, df in excel_data.items():
        # Bereinigen des Tabellennamens (Leerzeichen durch Unterstriche ersetzen)
        table_name = sheet_name.replace(" ", "_")

        # In die Datenbank schreiben
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Blatt '{sheet_name}' wurde als Tabelle '{table_name}' in {db_file} gespeichert.")

    conn.close()
    print("Konvertierung abgeschlossen!")


# Usage
excel_file = '260625_slab_properties.xlsx'
db_file = '260625_slab_properties.db'
excel_to_db(excel_file, db_file)