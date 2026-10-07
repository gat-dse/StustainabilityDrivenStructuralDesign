import pandas as pd

# ==============================================================================
# CONFIGURATION & FILE HANDLING
# ==============================================================================
input_file = "260625_1654_Members.xlsx"
output_file = "260625_1654_Members_Mean.xlsx"

print(f"Lese Master-Datenbank ein: {input_file}")
df = pd.read_excel(input_file)

# Falls Spalten führende oder nachstehende Leerzeichen haben, diese säubern
df.columns = df.columns.str.strip()

# ==============================================================================
# AGGREGATIONSLOGIK DEFINIEREN
# ==============================================================================
# Wir gruppieren nach dem 'plot_label' UND der Spannweite
group_columns = ['plot_label', 'l_tot [m]']

for col in group_columns:
    if col not in df.columns:
        raise ValueError(f"Die erforderliche Spalte '{col}' wurde in der Excel-Datei nicht gefunden!")

aggregation_dict = {}

for col in df.columns:
    # Die Spalten, nach denen gruppiert wird, fließen nicht in das Aggregations-Dict
    if col in group_columns:
        continue

    # Versuche die Spalte numerisch zu interpretieren
    numeric_col = pd.to_numeric(df[col], errors='coerce')

    # Wenn die Spalte überwiegend Zahlen enthält, berechne den Mittelwert (MEAN)
    if numeric_col.notna().sum() > (len(df) * 0.5):
        df[col] = numeric_col
        aggregation_dict[col] = 'mean'
    else:
        # Bei Textspalten (Strings, Kategorien) behalten wir den ersten Eintrag
        aggregation_dict[col] = 'first'

# ==============================================================================
# MITTELWERTE PRO SPANNWEITE BERECHNEN & SPEICHERN
# ==============================================================================
print(f"Gruppiere Daten nach {group_columns} und berechne Mittelwerte...")

# Aggregieren (as_index=False hält die Gruppierungsspalten als normale Tabellenspalten)
df_mean = df.groupby(group_columns, as_index=False).agg(aggregation_dict)

# Spaltenreihenfolge wie im Original-DataFrame wiederherstellen
# (Gruppierungsspalten nach vorne, gefolgt von den restlichen Spalten)
remaining_cols = [col for col in df.columns if col not in group_columns]
df_mean = df_mean[group_columns + remaining_cols]

# Sortieren für eine saubere Übersicht (erst nach System, dann nach Spannweite aufsteigend)
df_mean = df_mean.sort_values(by=group_columns).reset_index(drop=True)

# Ergebnis als neue Excel-Datei speichern
df_mean.to_excel(output_file, index=False)

print("\n==================================================")
print(f"DONE! Aggregierte MEAN-Datenbank (pro Spannweite) erfolgreich erstellt.")
print(f"Datei: {output_file}")
print(f"Anzahl generierter Datenpunkte (Zeilen): {df_mean.shape[0]}")
print("==================================================")