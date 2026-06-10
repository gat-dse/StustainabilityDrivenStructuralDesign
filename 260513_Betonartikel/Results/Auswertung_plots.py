import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# PART 1: EINZELPLOT (GWP TOTAL)
# ==============================================================================

# 1. Datei über absoluten Pfad einlesen
excel_file = "260604_RC_1D_Systems.xlsx"
df = pd.read_excel(excel_file)

# --- DIAGNOSE-PRINT ---
print("=" * 60)
print("DEINE EXCEL-SPALTEN SIND:")
print(df.columns.tolist())
print("=" * 60)
# ----------------------

# 2. Daten bereinigen und konvertieren
x_achse = 'l_tot [m]'
y_achse = 'co2 [kgco2eq/m2]'
kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_achse] = pd.to_numeric(df[y_achse], errors='coerce')

df_single = df.dropna(subset=[x_achse, y_achse, kategorie_1, kategorie_2]).copy()
df_single = df_single.sort_values(x_achse)

# 3. Plot erstellen
plt.figure(figsize=(11, 7))
sns.set_theme(style="whitegrid")

# Wir fangen den aktuellen Achsen-Kontext (ax) ab, um ihn zu manipulieren
ax_single = sns.lineplot(
    data=df_single,
    x=x_achse,
    y=y_achse,
    hue=kategorie_1,
    style=kategorie_2,
    marker='o',
    errorbar=("pi", 100),
    estimator='mean',
    palette='viridis',
    linewidth=2
)

# HIER ERZWINGEN WIR DIE 0 FÜR DEN EINZELPLOT:
ax_single.set_ylim(bottom=0)

# 4. Titel und Achsen beschriften
plt.title("GWP total für Betonquerschnitte", fontsize=14, fontweight='bold')
plt.xlabel("Spannweite [m]", fontsize=12)
plt.ylabel(r"GWP$_{total}$ [kg CO$_{2eq}$ / m$^2$]", fontsize=12)

plt.legend(title=r"Betonfestigkeit (f$_{ck}$)", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid(True, linestyle='--', alpha=0.5)

# ==============================================================================
# PART 2: SUBPLOTS (3x2 MULTIKRITERIEN-ANALYSE)
# ==============================================================================

# Gesamtes CO2 berechnen (Struktur + Bodenaufbau)
df['co2 Total_berechnet [kgCO2eq/m2]'] = df['co2 Struktur [kgCO2eq/m2]'] + df['co2 Bodenaufbau [kgCO2eq/m2]']

ziel_werte = [
    'h_QS [m]',
    'h_tot [m]',
    'Last Struktur [kN/m2]',
    'Last_tot [kN/m2]',
    'co2 Struktur [kgCO2eq/m2]',
    'co2 Total_berechnet [kgCO2eq/m2]'
]

label_mapping = {
    'h_QS [m]': r"h$_{struc}$ [m]",
    'h_tot [m]': r"h$_{tot}$ [m]",
    'Last Struktur [kN/m2]': r"Last$_{struc}$ [kN/m$^2$]",
    'Last_tot [kN/m2]': r"Last$_{tot}$ [kN/m$^2$]",
    'co2 Struktur [kgCO2eq/m2]': r"GWP$_{struc}$ [kg CO$_2$-eq/m$^2$]",
    'co2 Total_berechnet [kgCO2eq/m2]': r"GWP$_{tot}$ [kg CO$_2$-eq/m$^2$]"
}

df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
for wert in ziel_werte:
    df[wert] = pd.to_numeric(df[wert], errors='coerce')

pflicht_spalten = [x_achse, kategorie_1, kategorie_2] + ziel_werte
df_subplots = df.dropna(subset=pflicht_spalten).copy()
df_subplots = df_subplots.sort_values(x_achse)

fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 10))
sns.set_theme(style="whitegrid")
axes_flat = axes.flatten()

for i, aktueller_y_wert in enumerate(ziel_werte):
    ax = axes_flat[i]

    sns.lineplot(
        data=df_subplots,
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

    schoenes_label = label_mapping.get(aktueller_y_wert, aktueller_y_wert)
    ax.set_ylabel(schoenes_label, fontsize=11, fontweight='bold')
    ax.set_xlabel("Spannweite [m]", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)

    # HIER ERZWINGEN WIR DIE 0 FÜR JEDEN SUBPLOT VORAB:
    ax.set_ylim(bottom=0)

# ------------------------------------------------------------------------------
# ACHSENBEREICHE SYNCHRONISIEREN (Unter Beibehaltung der 0 als Minimum)
# ------------------------------------------------------------------------------
# Diagramm 1 und 2 (Index 0 und 1) angleichen
ymax_last = max(axes_flat[0].get_ylim()[1], axes_flat[1].get_ylim()[1])
axes_flat[0].set_ylim(0, ymax_last)
axes_flat[1].set_ylim(0, ymax_last)

# Diagramm 3 und 4 (Index 2 und 3) angleichen
ymax_co2 = max(axes_flat[2].get_ylim()[1], axes_flat[3].get_ylim()[1])
axes_flat[2].set_ylim(0, ymax_co2)
axes_flat[3].set_ylim(0, ymax_co2)
# ------------------------------------------------------------------------------

# --- LEGENDE EXTRAHIEREN ---
handles, labels = axes_flat[0].get_legend_handles_labels()

for ax in axes_flat:
    if ax.get_legend():
        ax.get_legend().remove()

fig.legend(
    handles,
    labels,
    title=r"System-Spezifikation / Querschnitt",
    loc="center left",
    bbox_to_anchor=(0.78, 0.5),
    fontsize='x-small',
    title_fontsize='small'
)

fig.suptitle("Multikriterien-Analyse für Betonquerschnitte", fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 0.75, 0.95])

plt.show()