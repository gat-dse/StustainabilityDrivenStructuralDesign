
import sqlite3

conn = sqlite3.connect("database_260506_Hochbau.db")
cursor = conn.cursor()

# Test 1: Gibt es überhaupt 'Steel_reinforcing_bar'?
cursor.execute("SELECT COUNT(*) FROM products WHERE MATERIAL LIKE '%Steel_reinforcing_bar%'")
print("Anzahl Steel_reinforcing_bar gesamt:", cursor.fetchone()[0])

# Test 2: Wie viele erfüllen die Festigkeit 'B500B'?
cursor.execute("SELECT COUNT(*) FROM products WHERE MATERIAL LIKE '%Steel_reinforcing_bar%' AND MECH_PROP = 'B500B'")
print("Anzahl mit MECH_PROP = 'B500B':", cursor.fetchone()[0])

# Test 3: Welche Werte haben die Filter-Flags bei diesen Stählen?
cursor.execute("""
    SELECT ValidEPD, MIN_MAX, Man_Ausschluss, COUNT(*) 
    FROM products 
    WHERE MATERIAL LIKE '%Steel_reinforcing_bar%' 
    GROUP BY ValidEPD, MIN_MAX, Man_Ausschluss
""")
print("\nVerteilung der Filter-Flags (ValidEPD, MIN_MAX, Man_Ausschluss, Anzahl):")
for row in cursor.fetchall():
    print(row)

conn.close()