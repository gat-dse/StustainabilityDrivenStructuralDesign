#Packages: pip install pandas openpyxl
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns



target_columns = [
    "Member_ID",
    "criteria",
    "section_type",
    "Statisches System",
    "l_tot [m]",
    "h_QS [m]",  # Ohne das Leerzeichen am Ende!
    "b [m]",
    "b_w [m]",
    "h_f [m]",
    "concrete_type",
    "mech_prop",
    "prod_id",
    "GWP concrete [kgCO2eq / t]",
    "rebar_type",
    "mech_prop_1",
    "prod_id_1",
    "GWP rebar [kgCO2eq / t]",
    "co2_rebar [kgCO2eq/m2]",
    "co2_concrete [kgCO2eq/m2]",
    "co2 Struktur [kgCO2eq/m2]",
    "Bodenaufbau",
    "lifespan Estrich [a]",
    "h_Bodenaufbau [m]",
    "co2 Bodenaufbau [kgCO2eq/m2]",
    "co2 Bodenaufbau pro Jahr [kgCO2eq / m2a]",
    "Last Struktur [kN/m2]",
    "Last Bodenaufbau [kN/m2]",
    "co2 Total [kgCO2eq / m2]",
    "co2 Total pro Jahr [kgCO2eq / m2a]",
]

# 1. Excel Files definieren
excel_files = [
    "Members_simple_rc_rec_150_clean.xlsx",
    "Members_simple_rc_rib_150_clean.xlsx",
    "Members_simple_rc_rec_150_var_clean.xlsx",
    "Members_continuous_rc_rec_150_clean.xlsx",
]

# Liste, in der wir die vorbereiteten DataFrames sammeln
cleaned_dfs = []

# 2. Files einlesen, bereinigen und auf Ziel-Struktur bringen
for file in excel_files:
    # Excel einlesen
    df = pd.read_excel(file)

    # Spaltennamen von unsichtbaren Leerzeichen befreien (z.B. 'h_QS [m] ' -> 'h_QS [m]')
    df.columns = df.columns.str.strip()

    # HIER PASSIERT DIE MAGIE:
    # reindex wirft alle Spalten raus, die nicht in target_columns stehen,
    # fügt fehlende Spalten als leere Spalten hinzu und bringt alles in die exakte Reihenfolge.
    df_reindexed = df.reindex(columns=target_columns)

    cleaned_dfs.append(df_reindexed)

# 3. Alle perfekt formatierten Tabellen untereinanderkopieren
df_final = pd.concat(cleaned_dfs, axis=0, ignore_index=True)

# 4. Spalte ergänzen als Kombination aus zwei bestehenden Spalten
df_final.insert(2, 'plot_label', '')
# Erstellt ein Label für Beschreibung der Members
df_final['plot_label'] = df_final['Statisches System'] + "_" + df_final['section_type'] + "_" + df_final['Bodenaufbau']


#5. Neue spalte für Gesamte Querschnittshöhe
df_final.insert(21, 'h_tot [m]', df_final['h_QS [m]'] + df_final['h_Bodenaufbau [m]'])

#6. Anpassung Einheit für Lasten von [N/m2] in [kN/m2]
df_final['Last Struktur [kN/m2]'] = df_final.pop('Last Struktur [N/m2]') / 1000
df_final['Last Bodenaufbau [kN/m2]'] = df_final.pop('Last Bodenaufbau [N/m2]') / 1000

#6. Neue spalte für Gesamte Last am Ende ergänzen
df_final['Last_tot [kN/m2]'] = df_final['Last Struktur [kN/m2]'] + df_final['Last Bodenaufbau [kN/m2]']

# 7. Korrektur für GWP Member
df_final['co2 Total [kgCO2eq / m2]'] = df_final['co2 Total [kgCO2eq / m2]'] / df_final['l_tot [m]']
df_final['co2 Total pro Jahr [kgCO2eq / m2a]'] = df_final['co2 Total pro Jahr [kgCO2eq / m2a]'] / df_final['l_tot [m]']



# 7. Speichern
output_file = "260520_Iteration150_total.xlsx"
df_final.to_excel(output_file, index=False)

print(
    f"Die finale Tabelle hat {len(target_columns)} definierten Spalten."
)

print(
    f"Die finale Tabelle hat {len(df_final)} definierten Zeilen."
)