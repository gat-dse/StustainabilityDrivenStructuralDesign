import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# 1. DATEI ÜBER ABSOLUTEN PFAD EINLESEN
# ==============================================================================
excel_file = "260604_RC_1D_Systems.xlsx"
df = pd.read_excel(excel_file)
# Extrahiert den Namen ohne ".xlsx"
file_name_base = os.path.splitext(os.path.basename(excel_file))[0]

# --- DIAGNOSE-PRINT (Zeigt dir deine echten Spalten im Terminal) ---
print("="*60)
print("DEINE EXCEL-SPALTEN SIND:")
print(df.columns.tolist())
print("="*60)
# ------------------------------------------------------------------

# ==============================================================================
# 2. DEFINITION DER ACHSEN UND KATEGORIEN (EINZELPLOT)
# ==============================================================================
x_achse = 'l_tot [m]'
y_achse = 'h_QS [m]'
kategorie_1 = 'plot_label'
kategorie_2 = 'Statisches System'

df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_achse] = pd.to_numeric(df[y_achse], errors='coerce')

# Zeilen ohne gültige CO2- oder Spannweiten-Werte löschen
df = df.dropna(subset=[x_achse, y_achse, kategorie_1, kategorie_2])

# Sortieren für eine saubere Linienführung
df = df.sort_values(x_achse)

# ==============================================================================
# 3. ERSTEN EINZELPLOT ERSTELLEN
# ==============================================================================
plt.figure(figsize=(11, 7))
sns.set_theme(style="whitegrid")

sns.lineplot(
    data=df,
    x=x_achse,
    y=y_achse,
    hue=kategorie_1,      # Farbe
    style=kategorie_2,    # Linienstil
    marker='o',
    errorbar=("pi", 0),
    estimator='mean',
    palette='viridis',
    linewidth=2
)

# Titel und Achsen beschriften
plt.title("GWP total für Betonrechteckquerschnitte", fontsize=14, fontweight='bold')
plt.xlabel("Spannweite [m]", fontsize=12)
plt.ylabel("CO2 Total [kgCO2-eq / m2]", fontsize=12)

# Achsenschnittpunkt exakt bei y=0 und x-Startwert festlegen
plt.ylim(bottom=0)
plt.xlim(left=df[x_achse].min(), right=df[x_achse].max())

plt.legend(title="Betonfestigkeit", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid(True, linestyle='--', alpha=0.5)

# AUTOMATISCH SPEICHERN: Einzelplot (300 dpi für scharfe Grafiken)
single_plot_name = f"{file_name_base}_GWP_single_plot.png"
plt.savefig(single_plot_name, dpi=300, bbox_inches='tight')
print(f"-> Einzelplot erfolgreich gespeichert unter: {single_plot_name}")

plt.show()


# ==============================================================================
# 4. DATA PREPARATION FÜR SUBPLOTS (MULTIKRITERIEN-ANALYSE)
# ==============================================================================
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

# Daten bereinigen und numerisch konvertieren
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
for wert in ziel_werte:
    df[wert] = pd.to_numeric(df[wert], errors='coerce')

# Zeilen ohne gültige Werte löschen
pflicht_spalten = [x_achse, kategorie_1, kategorie_2] + ziel_werte
df = df.dropna(subset=pflicht_spalten)

# Sortieren für eine saubere Linienführung
df = df.sort_values(x_achse)

# ==============================================================================
# 5. SUBPLOTS IM 3 x 2 RASTER ERSTELLEN
# ==============================================================================
fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 10))
sns.set_theme(style="whitegrid")
axes_flat = axes.flatten()

# Schleife über alle Zielwerte, um die Subplots zu befüllen
for i, aktueller_y_wert in enumerate(ziel_werte):
    ax = axes_flat[i]

    sns.lineplot(
        data=df,
        x=x_achse,
        y=aktueller_y_wert,
        hue=kategorie_1,
        style=kategorie_2,
        dashes=True,          # Erzwingt, dass unterschiedliche section_types andere Striche bekommen
        markers=True,         # Gibt unterschiedlichen section_types auch andere Punkt-Formen (Kreis, Kreuz etc.)
        errorbar=("pi", 0),
        estimator='mean',
        palette='viridis',
        linewidth=1.5,
        ax=ax
    )

    # Achsenbeschriftung mit originalem Spaltennamen
    ax.set_ylabel(aktueller_y_wert, fontsize=11, fontweight='bold')
    ax.set_xlabel("Spannweite [m]", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Achsenschnittpunkt vorab für jeden Plot einzeln auf y=0 zwingen
    ax.set_ylim(bottom=0)
    ax.margins(x=0)

# ==============================================================================
# 6. ACHSENBEREICHE PAARWEISE SYNCHRONISIEREN (Harter Nullpunkt fixiert)
# ==============================================================================
# Paar 1: Bauteilhöhen (Index 0 und 1)
ymax_h = max(axes_flat[0].get_ylim()[1], axes_flat[1].get_ylim()[1])
axes_flat[0].set_ylim(0, ymax_h)
axes_flat[1].set_ylim(0, ymax_h)

# Paar 2: Lasten (Index 2 und 3)
ymax_last = max(axes_flat[2].get_ylim()[1], axes_flat[3].get_ylim()[1])
axes_flat[2].set_ylim(0, ymax_last)
axes_flat[3].set_ylim(0, ymax_last)

# Paar 3: CO2-Werte (Index 4 und 5)
ymax_co2 = max(axes_flat[4].get_ylim()[1], axes_flat[5].get_ylim()[1])
axes_flat[4].set_ylim(0, ymax_co2)
axes_flat[5].set_ylim(0, ymax_co2)

# Absolute Sicherheit für den Nullpunkt
for ax in axes_flat:
    ax.set_ylim(bottom=0)
# ==============================================================================

# ==============================================================================
# 7. LEGENDE EXTRAHIEREN & LAYOUT FINALE (KORRIGIERT FÜR HUE & STYLE)
# ==============================================================================
# Wir holen die echten Labels und Handles des ersten Plots, BEVOR wir sie löschen
handles, labels = axes_flat[0].get_legend_handles_labels()

# Einzelne Legenden in den Subplots löschen
for ax in axes_flat:
    if ax.get_legend():
        ax.get_legend().remove()

# Globale Legende am rechten Rand platzieren
# Matplotlib baut hier nun die Sektionen für plot_label UND section_type untereinander auf
fig.legend(
    handles,
    labels,
    title="System & Querschnittstyp",
    loc="center left",
    bbox_to_anchor=(0.78, 0.5),
    fontsize='x-small',
    title_fontsize='small'
)

# Gesamttitel für die Grafik
fig.suptitle("Multikriterien-Analyse für Betonquerschnitte", fontsize=16, fontweight='bold', y=0.98)

# Layout optimieren (Platz für die rechte Legende lassen)
plt.tight_layout(rect=[0, 0, 0.75, 0.95])

# DYNAMISCH SPEICHERN: Verknüpft mit dem Excel-Dateinamen
matrix_plot_name = f"{file_name_base}_h_Last_GWP_Analysis.png"
plt.savefig(matrix_plot_name, dpi=300, bbox_inches='tight')
print(f"-> Multikriterien-Matrix erfolgreich gespeichert unter: {matrix_plot_name}")

# Plot anzeigen
plt.show()


