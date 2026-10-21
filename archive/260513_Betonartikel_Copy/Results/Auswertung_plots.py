import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# PART 1: EINZELPLOT (GWP TOTAL)
# ==============================================================================

# 1. Datei über absoluten Pfad einlesen
excel_file = "260611_0934_Members.xlsx"
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

# WICHTIGE KORREKTUR: Zuerst nach 'plot_label' und dann nach der X-Achse sortieren
df_single = df_single.sort_values(by=[kategorie_1, x_achse])

# --- EXAKTES FARBMAPPING ---
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': '#1f77b4',  # Dunkelblau
    'BeamContinuousSupEl_rc_rec_massiv': '#6baed6',      # Hellblau
    'BeamSimpleSup_rc_rec_Schuettung': '#2ca02c',        # Dunkelgrün
    'BeamSimpleSup_rc_rec_massiv': '#a1d99b'            # Hellgrün
}

# Mapping für den Linienstil (durchgezogen für Schuettung, gestrichelt für massiv)
stil_mapping = {
    'Schuettung': '-',
    'massiv': '--'
}

# --- NEU: MANUELLES MAPPING FÜR DIE LEGENDEN-NAMEN ---
legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': 'Durchlaufträger, Rechteck-QS Beton (+ Schüttung)',
    'BeamContinuousSupEl_rc_rec_massiv': 'Durchlaufträger, Rechteck-QS Beton',
    'BeamSimpleSup_rc_rec_Schuettung': 'Einfeldträger, Rechteck-QS Beton (+ Schüttung)',
    'BeamSimpleSup_rc_rec_massiv': 'Einfeldträger, Rechteck-QS Beton'
}

# 3. Plot erstellen
plt.figure(figsize=(11, 7))
sns.set_theme(style="whitegrid")

# ANPASSUNG: Aggregation erweitert um min und max für die Streuungsfläche
df_single_grouped = df_single.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[y_achse].agg(['mean', 'min', 'max'])

# Wir plotten die Linien einzeln pro System, um die Legende perfekt zu kontrollieren
for label, g in df_single_grouped.groupby(kategorie_1):
    bodenaufbau = g[kategorie_2].iloc[0]
    farbe = farb_mapping.get(label, '#7f7f7f')

    # Schönen Namen aus dem Mapping holen
    schoener_name = legend_label_mapping.get(label, label)

    '''
    # 1. Streuungsband zeichnen (Bereich von min bis max)
    plt.fill_between(
        g[x_achse],
        g['min'],
        g['max'],
        color=farbe,
        alpha=0.15,          # Transparenz des Schattens (0.15 = 15% Deckkraft)
        label='_nolegend_'   # Taucht nicht extra in der Legende auf
    )'''

    # 2. Saubere Hauptlinie (Mittelwert) zeichnen
    plt.plot(
        g[x_achse],
        g['mean'],
        marker='o',
        markersize=5,
        markeredgewidth=0.5,
        color=farbe,
        linestyle=stil_mapping.get(bodenaufbau, '-'),
        linewidth=2,
        label=schoener_name
    )

plt.ylim(bottom=0)

# 4. Titel und Achsen beschriften
plt.title("GWP total inkl. Datenstreuung (Min-Max-Bereich)", fontsize=14, fontweight='bold')
plt.xlabel("Spannweite [m]", fontsize=12)
plt.ylabel(r"GWP$_{total}$ [kg CO$_{2eq}$ / m$^2$]", fontsize=12)

# Legende erstellen
plt.legend(title="System, Querschnitt und Bodenaufbau", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid(True, linestyle='--', alpha=0.5)


# ==============================================================================
# PART 2: SUBPLOTS (3x2 MULTIKRITERIEN-ANALYSE) - Bleibt unverändert sauber
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

# Sortieren
df_subplots = df_subplots.sort_values(by=[kategorie_1, x_achse])

fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 10))
sns.set_theme(style="whitegrid")
axes_flat = axes.flatten()

for i, aktueller_y_wert in enumerate(ziel_werte):
    ax = axes_flat[i]

    # Daten aggregieren
    df_subplots_grouped = df_subplots.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[aktueller_y_wert].mean()

    # Manuelles Plotten der Gruppen auf dem jeweiligen Subplot-Achsenobjekt (ax)
    for label, g in df_subplots_grouped.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]

        # Schönen Namen aus dem Mapping holen
        schoener_name = legend_label_mapping.get(label, label)

        ax.plot(
            g[x_achse],
            g[aktueller_y_wert],
            marker='o',
            markersize=3.5,
            markeredgewidth=0.3,
            color=farb_mapping.get(label, '#7f7f7f'),
            linestyle=stil_mapping.get(bodenaufbau, '-'),
            linewidth=1.5,
            label=schoener_name
        )

    schoenes_label = label_mapping.get(aktueller_y_wert, aktueller_y_wert)
    ax.set_ylabel(schoenes_label, fontsize=11, fontweight='bold')
    ax.set_xlabel("Spannweite [m]", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_ylim(bottom=0)

# ------------------------------------------------------------------------------
# ACHSENBEREICHE SYNCHRONISIEREN
# ------------------------------------------------------------------------------
ymax_last = max(axes_flat[0].get_ylim()[1], axes_flat[1].get_ylim()[1])
axes_flat[0].set_ylim(0, ymax_last)
axes_flat[1].set_ylim(0, ymax_last)

ymax_co2 = max(axes_flat[2].get_ylim()[1], axes_flat[3].get_ylim()[1])
axes_flat[2].set_ylim(0, ymax_co2)
axes_flat[3].set_ylim(0, ymax_co2)
# ------------------------------------------------------------------------------

# --- GLOBAL LEGENDE EXTRAHIEREN ---
handles, labels = axes_flat[0].get_legend_handles_labels()

# Sortiert die Legenden-Einträge alphabetisch nach dem neuen, schönen Namen
sorted_legend = sorted(zip(handles, labels), key=lambda t: t[1])
if sorted_legend:
    handles_sorted, labels_sorted = zip(*sorted_legend)
else:
    handles_sorted, labels_sorted = [], []

# Globale Legende am rechten Rand platzieren
fig.legend(
    handles_sorted,
    labels_sorted,
    title="System-Spezifikation / Querschnitt",
    loc="center left",
    bbox_to_anchor=(0.78, 0.5),
    fontsize='small',
    title_fontsize='medium'
)

# Einzelne Legenden in den Subplots löschen
for ax in axes_flat:
    if ax.get_legend():
        ax.get_legend().remove()

fig.suptitle("Multikriterien-Analyse für Betonquerschnitte", fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 0.75, 0.95])

plt.show()