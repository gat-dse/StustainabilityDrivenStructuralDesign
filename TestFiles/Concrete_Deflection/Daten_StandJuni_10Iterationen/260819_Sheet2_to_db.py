"""
Liest das Excel-Sheet "Sheet2" aus 260603_Members_rc_rec_2_10Iterationen_Anm260813.xlsx ein,
transponiert die Tabelle (Zeilen <-> Spalten, sodass jede Zeile einem "Member_xxx" entspricht)
und speichert das Ergebnis als SQLite-Datenbank (Tabelle "members").
"""
import sqlite3

import pandas as pd

excel_file = "260603_Members_rc_rec_2_10Iterationen_Anm260813.xlsx"
sheet_name = "Sheet2"
db_file = "260603_Members_rc_rec_2_10Iterationen_Sheet2.db"
table_name = "members"

# ==============================================================================
# EINLESEN & TRANSPONIEREN
# ==============================================================================
df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

# Spalte A enthält die Attributnamen (key), Spalte B ff. je einen Member
keys = df_raw.iloc[1:, 0]
data = df_raw.iloc[1:, 1:]
member_ids = df_raw.iloc[0, 1:]

df_t = data.set_axis(keys, axis=0).set_axis(member_ids, axis=1).T
df_t.index.name = "Member_ID"
df_t = df_t.reset_index()

# Spaltennamen eindeutig machen bei Duplikaten (z.B. 'h' und 'wger / wi' kommen mehrfach vor)
cols = pd.Series(df_t.columns.astype(str))
for name in cols[cols.duplicated()].unique():
    dup_idx = cols[cols == name].index
    cols[dup_idx] = [f"{name}_{i}" if i != 0 else name for i in range(len(dup_idx))]
df_t.columns = cols

# ==============================================================================
# SPEICHERN ALS SQLITE-DATENBANK
# ==============================================================================
con = sqlite3.connect(db_file)
df_t.to_sql(table_name, con, if_exists="replace", index=False)
con.close()

print(f"Datenbank erfolgreich erstellt: {db_file}")
print(f"Tabelle '{table_name}': {df_t.shape[0]} Zeilen (Members) x {df_t.shape[1]} Spalten")
