#Packages: pip install pandas openpyxl
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns

#Datentabelle Cleaning als Funktion schreiben und dann für alle Excel ausführen.
#Als zweiten Schritt alle Exceltabellen in einer Tabelle zusammenführen für die Plots

#1. Excel File einlesen:
# 1.1. Load the Excel file
excel_file = "Members_rc_rib_2.xlsx"
df = pd.read_excel(excel_file)
# 1. Den Namen dynamisch generieren
file_name_base = os.path.splitext(excel_file)[0]
output_file = f"{file_name_base}_clean.xlsx"

# Transponieren, damit Member Zeilen werden
# Wir setzen 'key' und 'level' als Index, damit sie beim Drehen erhalten bleiben
df_clean = df.set_index(['key', 'level']).T
df_clean.index.name = 'Member_ID'
df_clean.columns = df_clean.columns.get_level_values(0)
df_clean = df_clean.reset_index()


#2. File bereinigen:
#Spalten Namen umbenennen, sodass sie einduetig sind
cols = pd.Series(df_clean.columns)
for i in cols[cols.duplicated()].unique():
    # Findet alle Stellen mit dem Namen 'i' und hängte eine Nummer an
    cols[cols[cols == i].index] = [f"{i}_{count}" if count != 0 else i
                                   for count in range(len(cols[cols == i]))]
df_clean.columns = cols

#Relevante Spalten definieren
if 'rc_rec' in df_clean['section_type'].values:
    spalten_fokus = ['Member_ID', 'section_type', 'l_tot', 'h', 'b', 'concrete_type', 'mech_prop', 'prod_id', 'GWP',
                     'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP_1', 'co2_rebar', 'co2_concrete', 'co2',
                     'system',
                     'h_4', 'co2_4', 'co2_a_3', 'g0k_1', 'g1k', 'co2_5', 'co2_a_4']
    Spalten_Neu = ['Member_ID', 'section_type', 'l_tot [m]', 'h_QS [m] ', 'b [m]', 'concrete_type', 'mech_prop',
                   'prod_id', 'GWP', 'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP_1 [kgCO2eq / t]',
                   'co2_rebar [kgCO2eq/m2]', 'co2_concrete [kgCO2eq/m2]', 'co2 Struktur [kgCO2eq/m2]',
                   'system',
                   'h_Bodenaufbau [m]', 'co2 Bodenaufbau [kgCO2eq/m2]', 'co2 Bodenaufbau pro Jahr [kgCO2eq / m2a]',
                   'Last Struktur [kN/m2]', 'Last Bodenaufbau [kN/m2]', 'co2 Total [kgCO2eq / m2]',
                   'co2 Total pro Jahr [kgCO2eq / m2a]']

if 'rc_rib' in df_clean['section_type'].values:
    spalten_fokus = ['Member_ID', 'section_type', 'l_tot', 'h', 'b', 'b_w', 'hf_' 
                     'concrete_type', 'mech_prop', 'prod_id', 'GWP',
                     'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP_1', 'co2_rebar', 'co2_concrete', 'co2',
                     'system',
                     'h_5', 'co2_5', 'co2_a_4', 'g0k_1', 'g1k', 'co2_6', 'co2_a_5']
    Spalten_Neu = ['Member_ID', 'section_type', 'l_tot [m]', 'h_QS [m] ', 'b [m]' ,'b_w [m]', 'h_f [m]'
                   'concrete_type', 'mech_prop', 'prod_id', 'GWP', 'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP_1 [kgCO2eq / t]',
                   'co2_rebar [kgCO2eq/m2]', 'co2_concrete [kgCO2eq/m2]', 'co2 Struktur [kgCO2eq/m2]',
                   'Statisches System',
                   'h_Bodenaufbau [m]', 'co2 Bodenaufbau [kgCO2eq/m2]', 'co2 Bodenaufbau pro Jahr [kgCO2eq / m2a]',
                   'Last Struktur [kN/m2]', 'Last Bodenaufbau [kN/m2]', 'co2 Total [kgCO2eq / m2]',
                   'co2 Total pro Jahr [kgCO2eq / m2a]']


# 2. Schritt: NUR die Spalten aus 'spalten_fokus' behalten
# intersection stellt sicher, dass wir nur Spalten nehmen, die auch wirklich existieren
df_final = df_clean[df_clean.columns.intersection(spalten_fokus)].copy()

# 3. Schritt: Dictionary erstellen
rename_dict = dict(zip(spalten_fokus, Spalten_Neu))

# 4. Schritt: Umbenennen
df_final = df_final.rename(columns=rename_dict)

# 5. Schritt: Sicherheitshalber die Reihenfolge erzwingen (löscht alle Reste)
# Wir filtern hier noch einmal nach den neuen Namen
df_final = df_final[[n for n in Spalten_Neu if n in df_final.columns]]

# Als Excel speichern
df_final.to_excel(output_file, index=False)

#---------------------------------------------------------------------------
#Plot erstellen:
# 1. Sicherstellen, dass die Daten numerisch sind
df_final['l_tot [m]'] = pd.to_numeric(df_final['l_tot [m]'], errors='coerce')
df_final['co2 Total [kgCO2eq / m2]'] = pd.to_numeric(df_final['co2 Total [kgCO2eq / m2]'], errors='coerce')

# WICHTIG: Damit die Linie sinnvoll verbindet, müssen die Daten nach der x-Achse sortiert sein
df_final = df_final.sort_values('l_tot [m]')

# 2. Plot erstellen mit relplot (kind='line' verbindet die Punkte)
g = sns.relplot(
    data=df_final,
    x='l_tot [m]',
    y='co2 Total [kgCO2eq / m2]',
    hue='section_type',      # Farbe nach Betongüte
    kind='line',          # Linien statt Regression
    marker='o',           # Fügt Punkte auf der Linie hinzu
    errorbar = ("pi", 100), #pi steht für Percentile Interval, 100 für Min bis Max
    palette='viridis',
    height=5,             # Etwas kleiner, damit nichts abgeschnitten wird
    aspect=1.5,
)

# 3. Titel und Achsen beschriften
g.set_axis_labels("Spannweite [m]", "CO2 Total [kgCO2eq / m2]")
g.figure.suptitle("GWP-Verlauf nach Spannweite", fontsize=14)
g.figure.subplots_adjust(top=0.9)

plt.grid(True, linestyle='--', alpha=0.5)
plt.show()