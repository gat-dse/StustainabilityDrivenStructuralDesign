import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Datei über absoluten Pfad einlesen
excel_file = "260520_Iteration150_total.xlsx"
df = pd.read_excel(excel_file)

# --- DIAGNOSE-PRINT (Zeigt dir deine echten Spalten im Terminal) ---
print("="*60)
print("DEINE EXCEL-SPALTEN SIND:")
print(df.columns.tolist())
print("="*60)
# ------------------------------------------------------------------

# 2. Daten bereinigen und konvertieren
x_achse = 'l_tot [m]'
y_achse = 'co2 Total [kgCO2eq / m2]'
kategorie_1 = 'plot_label'
kategorie_2 = 'mech_prop'

df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_achse] = pd.to_numeric(df[y_achse], errors='coerce')

# Zeilen ohne gültige CO2- oder Spannweiten-Werte löschen
df = df.dropna(subset=[x_achse, y_achse, kategorie_1, kategorie_2])

# Sortieren für eine saubere Linienführung
df = df.sort_values(x_achse)

# 3. Plot erstellen
plt.figure(figsize=(11, 7))
sns.set_theme(style="whitegrid")


sns.lineplot(
    data=df,
    x=x_achse,
    y=y_achse,
    hue=kategorie_1,      # Farbe
    style=kategorie_2,    # Linienstil
    marker='o',
    errorbar=("pi", 100),
    estimator='mean',
    palette='viridis',
    linewidth=2
)

# 4. Titel und Achsen beschriften
plt.title("GWP total für Betonquerschnitte", fontsize=14, fontweight='bold')
plt.xlabel("Spannweite [m]", fontsize=12)
plt.ylabel("CO2 Total [kgCO2eq / m2]", fontsize=12)

plt.legend(title="Betonfestigkeit", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid(True, linestyle='--', alpha=0.5)

# Plot anzeigen
#plt.show()






# 2. Definition der Achsen und Kategorien
x_achse = 'l_tot [m]'
kategorie_1 = 'plot_label'
kategorie_2 = 'mech_prop'


# Gesamtes CO2 berechnen (Struktur + Bodenaufbau)
df['co2 Total_berechnet [kgCO2eq/m2]'] = df['co2 Struktur [kgCO2eq/m2]'] + df['co2 Bodenaufbau [kgCO2eq/m2]']

# Die reinen Spaltennamen direkt als Liste für die Plots
ziel_werte = [
    'h_QS [m]',
    'h_tot [m]',
    'Last Struktur [kN/m2]',
    'Last_tot [kN/m2]',
    'co2 Struktur [kgCO2eq/m2]',
    'co2 Total_berechnet [kgCO2eq/m2]'
]

# 3. Daten bereinigen und numerisch konvertieren
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
for wert in ziel_werte:
    df[wert] = pd.to_numeric(df[wert], errors='coerce')

# Zeilen ohne gültige Werte löschen
pflicht_spalten = [x_achse, kategorie_1, kategorie_2] + ziel_werte
df = df.dropna(subset=pflicht_spalten)

# Sortieren für eine saubere Linienführung
df = df.sort_values(x_achse)

# 4. Subplots im n x 2 Raster erstellen
fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 10))

sns.set_theme(style="whitegrid")
axes_flat = axes.flatten()

# 5. Schleife über alle Zielwerte, um die Subplots zu befüllen
for i, aktueller_y_wert in enumerate(ziel_werte):
    ax = axes_flat[i]

    sns.lineplot(
        data=df,
        x=x_achse,
        y=aktueller_y_wert,
        hue=kategorie_1,
        style=kategorie_2,
        marker='o',
        errorbar=("pi", 0),
        estimator='mean',
        palette='viridis',
        linewidth=1,
        ax=ax
    )

    # Achsenbeschirftung mit originalem Spaltennamen
    ax.set_ylabel(aktueller_y_wert, fontsize=11, fontweight='bold')
    ax.set_xlabel("Spannweite [m]", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)

# ==============================================================================
# NUR ACHSENBEREICHE SYNCHRONISIEREN (Titel bleiben unberührt)
# ==============================================================================
# Diagramm 1 und 2 (Index 0 und 1) auf den gleichen Bereich setzen
ymin_last = min(axes_flat[0].get_ylim()[0], axes_flat[1].get_ylim()[0])
ymax_last = max(axes_flat[0].get_ylim()[1], axes_flat[1].get_ylim()[1])
axes_flat[0].set_ylim(ymin_last, ymax_last)
axes_flat[1].set_ylim(ymin_last, ymax_last)

# Diagramm 3 und 4 (Index 2 und 3) auf den gleichen Bereich setzen
ymin_co2 = min(axes_flat[2].get_ylim()[0], axes_flat[3].get_ylim()[0])
ymax_co2 = max(axes_flat[2].get_ylim()[1], axes_flat[3].get_ylim()[1])
axes_flat[2].set_ylim(ymin_co2, ymax_co2)
axes_flat[3].set_ylim(ymin_co2, ymax_co2)
# ==============================================================================

# --- LEGENDE EXTRAHIEREN ---
handles, labels = axes_flat[0].get_legend_handles_labels()

# Einzelne Legenden in den Plots löschen
for ax in axes_flat:
    if ax.get_legend():
        ax.get_legend().remove()

# Globale Legende am rechten Rand platzieren
fig.legend(
    handles,
    labels,
    title="Legende",
    loc="center left",
    bbox_to_anchor=(0.78, 0.5),
    fontsize='x-small',
    title_fontsize='small'
)

# Gesamttitel für die Grafik
fig.suptitle("Multikriterien-Analyse für Betonquerschnitte", fontsize=16, fontweight='bold', y=0.98)

# Layout optimieren
plt.tight_layout(rect=[0, 0, 0.75, 0.95])

# Plot anzeigen
plt.show()