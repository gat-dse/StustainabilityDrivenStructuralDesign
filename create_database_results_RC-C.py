#creates database for all the results of Rc-c (Rectangular-Concrete)
# units: [m], [kg], [s], [N], [CHF]

import pandas as pd
import sqlite3


def excel_to_sqlite(excel_file, db_name):
    # 1. Alle Tabellenblätter als Dictionary einlesen
    # sheet_name=None sorgt dafür, dass alle Blätter geladen werden
    sheets_dict = pd.read_excel(excel_file, sheet_name=None)

    # 2. Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect(db_name)

    # 3. Jedes Blatt als eigene Tabelle in die Datenbank schreiben
    for sheet_name, df in sheets_dict.items():
        # Leerzeichen im Tabellennamen durch Unterstriche ersetzen
        table_name = sheet_name.replace(' ', '_').lower()

        # DataFrame in SQL schreiben
        # if_exists='replace' löscht alte Tabellen mit gleichem Namen
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Tabelle '{table_name}' wurde erfolgreich erstellt. 📊")

    conn.close()
    print("Datenbank-Import abgeschlossen! ✅")


# Anwendung
excel_to_sqlite("deine_oekobilanz_daten.xlsx", "sustainability_v2.db")