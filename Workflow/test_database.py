import sqlite3

# Verbindung aufbauen
conn = sqlite3.connect("database_260506_Hochbau.db")
cursor = conn.cursor()

# HIER DIE KORRIGIERTE ABFRAGE MIT DATENTYP-UMWANDLUNG (CAST)
inquiry = """
SELECT PRO_ID, MECH_PROP, Total_GWP FROM products
WHERE "MATERIAL" = 'Steel_reinforcing_bar'
  AND DENSITY IS NOT NULL
  AND MECH_PROP = 'B500B'
  AND ValidEPD = 1
  AND Man_Ausschluss = 1
  AND CAST(Total_GWP AS REAL) IN (
      SELECT MIN(CAST(Total_GWP AS REAL)) FROM products 
      WHERE "MATERIAL" = 'Steel_reinforcing_bar' 
        AND DENSITY IS NOT NULL 
        AND MECH_PROP = 'B500B' 
        AND ValidEPD = 1 
        AND Man_Ausschluss = 1

      UNION

      SELECT MAX(CAST(Total_GWP AS REAL)) FROM products 
      WHERE "MATERIAL" = 'Steel_reinforcing_bar' 
        AND DENSITY IS NOT NULL 
        AND MECH_PROP = 'B500B' 
        AND ValidEPD = 1 
        AND Man_Ausschluss = 1
  )
"""

print("--- Ergebnis der NEUEN Abfrage ---")
cursor.execute(inquiry)
rows = cursor.fetchall()
if not rows:
    print("Keine Ergebnisse gefunden! Prüfe die Filtereinstellungen.")
else:
    for row in rows:
        print(row)


print("\n--- Inhalt von Zeile 115 und 118 zur Fehleranalyse ---")
# Diese Abfrage muss VOR dem conn.close() ausgeführt werden!
check_inquiry = """
SELECT rowid, PRO_ID, "MATERIAL", MECH_PROP, ValidEPD, Man_Ausschluss, Total_GWP 
FROM products 
WHERE PRO_ID IN ('115', '118') 
   OR rowid IN (115, 118)
"""

cursor.execute(check_inquiry)
check_rows = cursor.fetchall()
if not check_rows:
    print("Die Zeilen 115/118 konnten über diese IDs/Rowids nicht gefunden werden.")
else:
    for row in check_rows:
        print(f"Rowid/ID-Check: {row}")

# Verbindung ERST JETZT ganz am Ende schließen
conn.close()