#Packages: pip install pandas openpyxl

import pandas as pd
import sqlite3

# Pfad zur Excel-Datei (bitte anpassen!)
excel_file = "Members_rc_rec_2_test.xlsx"   #name of excel file. must be in same directory as code

# Excel-Datei einlesen
df_Members = pd.read_excel(excel_file, sheet_name="Members_Comparison)


# Verbindung zur SQLite-Datenbank herstellen (oder neu erstellen)
conn = sqlite3.connect("Members.db") #name of database

# Daten in die Datenbank schreiben
df_products.to_sql("products", conn, if_exists="replace", index=False)
df_material_prop.to_sql("material_prop", conn, if_exists="replace", index=False)
df_floor_struc_prop.to_sql("floor_struc_prop", conn, if_exists="replace", index=False)

# Verbindung schließen
conn.close()

print("Datenbank erfolgreich erstellt")
