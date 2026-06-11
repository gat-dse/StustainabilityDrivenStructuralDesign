import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# PART 1: EINZELPLOT (GWP TOTAL)
# ==============================================================================

# 1. Datei über absoluten Pfad einlesen
excel_file = "260611_1320_Members.xlsx"
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
    'BeamSimpleSup_rc_rec_massiv': '#a1d99b',            # Hellgrün
    'BeamSimpleSup_rc_rib_Schuettung': '#c39bd3',        # Lila/Violett für Rippe
    'BeamSimpleSup_rc_rib_massiv': '#9370db',             # Lila/Violett für Rippe

    'Slab_LL-eingespannt_rc_rec_massiv': '#b15928',       # Dunkelbraun/Rot
    'Slab_LL-eingespannt_rc_rec_Schuettung': '#fdbf6f',   # Helles Ocker
    'Slab_LL-frei_rc_rec_massiv': '#e31a1c',              # Kräftiges Rot
    'Slab_LL-frei_rc_rec_Schuettung': '#fb9a99'           # Hellrot/Rosa
}

# --- MARKER-MAPPING (Massive, unterscheidbare Formen) ---
marker_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': 'o',
    'BeamContinuousSupEl_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rec_Schuettung': 'o',
    'BeamSimpleSup_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rib_Schuettung': 'o',
    'BeamSimpleSup_rc_rib_massiv': 'o',

    'Slab_LL-eingespannt_rc_rec_massiv': 'v',
    'Slab_LL-eingespannt_rc_rec_Schuettung': 'v',
    'Slab_LL-frei_rc_rec_massiv': 'v',
    'Slab_LL-frei_rc_rec_Schuettung': 'v'
}


# --- LINIENSTIL-MAPPING ---
def get_linestyle_and_width(label, bodenaufbau):
    if 'Slab' in label:
        return ':', 1.0  # Dicht gepunktet für Platten
    elif bodenaufbau == 'Schuettung':
        return '-', 1.2  # Durchgezogen für Träger (Schüttung)
    else:
        return '--', 1.2  # Gestrichelt für Träger (massiv)


# --- MANUELLES MAPPING FÜR DIE LEGENDEN-NAMEN ---
legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': 'Durchlaufträger, Rechteck-QS (+ Schüttung)',
    'BeamContinuousSupEl_rc_rec_massiv': 'Durchlaufträger, Rechteck-QS (massiv)',
    'BeamSimpleSup_rc_rec_Schuettung': 'Einfeldträger, Rechteck-QS (+ Schüttung)',
    'BeamSimpleSup_rc_rec_massiv': 'Einfeldträger, Rechteck-QS (massiv)',
    'BeamSimpleSup_rc_rib_Schuettung': 'Einfeldträger, Plattenbalken-QS (+ Schüttung)',
    'BeamSimpleSup_rc_rib_massiv': 'Einfeldträger, Plattenbalken-QS (massiv)',
    'Slab_LL-eingespannt_rc_rec_Schuettung': 'Platte, eingespannt (+ Schüttung)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Platte, eingespannt (massiv)',
    'Slab_LL-frei_rc_rec_Schuettung': 'Platte, frei aufliegend (+ Schüttung)',
    'Slab_LL-frei_rc_rec_massiv': 'Platte, frei aufliegend (massiv)'

}

# 3. Plot erstellen
plt.figure(figsize=(11, 7))
sns.set_theme(style="whitegrid")

df_single_grouped = df_single.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[y_achse].agg(
    ['mean', 'min', 'max'])

for label, g in df_single_grouped.groupby(kategorie_1):
    bodenaufbau = g[kategorie_2].iloc[0]
    farbe = farb_mapping.get(label, '#7f7f7f')
    schoener_name = legend_label_mapping.get(label, label)

    # Linienstil und -dicke ermitteln
    l_style, l_width = get_linestyle_and_width(label, bodenaufbau)

    # 1. ERGÄNZT: Streuungsband zeichnen (Bereich von min bis max)
    plt.fill_between(
        g[x_achse],
        g['min'],
        g['max'],
        color=farbe,
        alpha=0.12,          # Transparenter, unaufdringlicher Hintergrundschatten
        label='_nolegend_'   # Wird in der Legende ignoriert
    )

    # 2. Saubere Hauptlinie (Mittelwert) zeichnen
    plt.plot(
        g[x_achse],
        g['mean'],
        marker=marker_mapping.get(label, 'o'),
        markersize=4,
        markeredgewidth=0.5,
        markeredgecolor='black',  # Jeder Marker kriegt die schwarze Kontur
        color=farbe,
        linestyle=l_style,
        linewidth=l_width,
        label=schoener_name
    )

plt.ylim(bottom=0)

plt.title("GWP total inkl. Datenstreuung (Min-Max-Bereich)", fontsize=14, fontweight='bold')
plt.xlabel("Spannweite [m]", fontsize=12)
plt.ylabel(r"GWP$_{total}$ [kg CO$_{2eq}$ / m$^2$]", fontsize=12)

plt.legend(title="System, Querschnitt und Bodenaufbau", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

# --- PART 1: GRID ANGEPASST (Fein und durchgezogen) ---
plt.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)

# ==============================================================================
# PART 2: SUBPLOTS (3x2 MULTIKRITERIEN-ANALYSE)
# ==============================================================================

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
df_subplots = df_subplots.sort_values(by=[kategorie_1, x_achse])

fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 10))
axes_flat = axes.flatten()

for i, aktueller_y_wert in enumerate(ziel_werte):
    ax = axes_flat[i]
    df_subplots_grouped = df_subplots.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[
        aktueller_y_wert].mean()

    for label, g in df_subplots_grouped.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        schoener_name = legend_label_mapping.get(label, label)

        # Linienstil und -dicke für die Subplots ermitteln
        l_style, l_width = get_linestyle_and_width(label, bodenaufbau)

        ax.plot(
            g[x_achse],
            g[aktueller_y_wert],
            marker=marker_mapping.get(label, 'o'),
            markersize=4,
            markeredgewidth=0.5,
            markeredgecolor='black',
            color=farb_mapping.get(label, '#7f7f7f'),
            linestyle=l_style,
            linewidth=l_width,
            label=schoener_name
        )

    schoenes_label = label_mapping.get(aktueller_y_wert, aktueller_y_wert)
    ax.set_ylabel(schoenes_label, fontsize=11, fontweight='bold')
    ax.set_xlabel("Spannweite [m]", fontsize=10)

    # --- PART 2: SUBPLOT-GRID ANGEPASST ---
    ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)

    ax.set_ylim(bottom=0)

# --- ACHSENBEREICHE SYNCHRONISIEREN ---
ymax_last = max(axes_flat[0].get_ylim()[1], axes_flat[1].get_ylim()[1])
axes_flat[0].set_ylim(0, ymax_last)
axes_flat[1].set_ylim(0, ymax_last)

ymax_co2 = max(axes_flat[4].get_ylim()[1], axes_flat[5].get_ylim()[1])
axes_flat[4].set_ylim(0, ymax_co2)
axes_flat[5].set_ylim(0, ymax_co2)

# --- GLOBAL LEGENDE EXTRAHIEREN ---
handles, labels = axes_flat[0].get_legend_handles_labels()
sorted_legend = sorted(zip(handles, labels), key=lambda t: t[1])
handles_sorted, labels_sorted = zip(*sorted_legend) if sorted_legend else ([], [])

fig.legend(
    handles_sorted,
    labels_sorted,
    title="System-Spezifikation / Querschnitt",
    loc="center left",
    bbox_to_anchor=(0.78, 0.5),
    fontsize='small',
    title_fontsize='medium'
)

for ax in axes_flat:
    if ax.get_legend():
        ax.get_legend().remove()

fig.suptitle("Multikriterien-Analyse für Betonquerschnitte", fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 0.75, 0.95])

plt.show()