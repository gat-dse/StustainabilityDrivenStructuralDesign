import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# ==============================================================================
# GLOBALE EINSTELLUNGEN & DATENPREPARATION
# ==============================================================================
excel_file = "260611_1515_Members.xlsx"
df = pd.read_excel(excel_file)

mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 14
mpl.rcParams['legend.fontsize'] = 12 # Etwas verkleinert für die 3-spaltige Legende

x_achse = 'l_tot [m]'
y_struc_h = 'h_QS [m]'
kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

# Datentypen erzwingen
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_struc_h] = pd.to_numeric(df[y_struc_h], errors='coerce')
df['h_f [m]'] = pd.to_numeric(df['h_f [m]'], errors='coerce')

# Bereinigen & Filtern: Spannweite 3 bis 12 m & NUR massiver Bodenaufbau
pflicht_spalten = [x_achse, kategorie_1, kategorie_2, y_struc_h]
df_clean = df.dropna(subset=pflicht_spalten).copy()

df_filtered = df_clean[
    (df_clean[x_achse].between(3, 12)) &
    (df_clean[kategorie_2].str.lower() == 'massiv')
].copy()

# Aggregation: Mittelwerte inkl. Flanschhöhe
df_grouped = df_filtered.groupby([x_achse, kategorie_1], as_index=False)[[y_struc_h, 'h_f [m]']].mean()

# ==============================================================================
# DESIGN-MAPPINGS
# ==============================================================================
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': '#000000',
    'BeamSimpleSup_rc_rec_massiv': '#2ca02c',
    'BeamSimpleSup_rc_rib_massiv': '#d8bfd8',
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042',
    'Slab_LL-frei_rc_rec_massiv': '#8b0000'
}

marker_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rib_massiv': 'o',
    'Slab_LL-eingespannt_rc_rec_massiv': '^',
    'Slab_LL-frei_rc_rec_massiv': '^'
}

legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'Vollplatte, einachsig tragend, durchlaufend\n(Standardaufbau)',
    'BeamSimpleSup_rc_rec_massiv': 'Vollplatte, einachsig tragend, einfach gelagert\n(Standardaufbau)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Vollplatte, zweiachsig tragend, durchlaufend\n(Standardaufbau)',
    'Slab_LL-frei_rc_rec_massiv': 'Vollplatte, zweiachsig tragend, einfach gelagert\n(Standardaufbau)',
    'BeamSimpleSup_rc_rib_massiv': 'Plattenbalken, einachsig tragend, einfach gelagert\n(Standardaufbau)'
}

# ==============================================================================
# PLOT GENERIEREN
# ==============================================================================
fig = plt.figure(figsize=(12, 8))
gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1, 0.25],
                      left=0.10, right=0.95, top=0.91, bottom=0.05, hspace=0.25)
ax = fig.add_subplot(gs[0])
ax_leg = fig.add_subplot(gs[1])
ax_leg.axis('off')

df_grouped = df_grouped.sort_values(by=[kategorie_1, x_achse])

for label, g in df_grouped.groupby(kategorie_1):
    farbe = farb_mapping.get(label, '#7f7f7f')
    schoener_name = legend_label_mapping.get(label, label)
    marker_style = marker_mapping.get(label, 'o')

    # Hauptlinie
    ax.plot(g[x_achse], g[y_struc_h], marker=marker_style, markersize=4,
            markeredgewidth=0.5, markeredgecolor='black', color=farbe,
            linestyle='-', linewidth=1.0, label=schoener_name)

    # Flanschhöhe für Plattenbalken
    if 'rib' in label:
        ax.plot(g[x_achse], g['h_f [m]'], color='#9370db',
                linestyle='-', linewidth=1.0, label='Plattenbalken, einachsig tragend, einfach gelagert\n(Standardaufbau), Flanschhöhe')

# Schallschutz-Referenz
h_schallschutz = 0.24
ax.axhline(y=h_schallschutz, color='#d32f2f', linestyle='--', linewidth=1.2,
           label='Mindeststärke für erhöhte\nSchallschutzanforderungen (24 cm)')

# Achsen-Design
ax.set_ylim(bottom=0)
ax.set_xlim(3, 12)
ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)
ax.set_axisbelow(True)
ax.set_title("Höhe Struktur $h_{struc}$ für Systeme mit Standardbodenaufbau", pad=15)
ax.set_xlabel("Spannweite [m]")
ax.set_ylabel("$h_{structure}$ [m]")

# Legenden-Logik (Dubletten entfernen & sortieren)
handles, labels = ax.get_legend_handles_labels()
unique_dict = {l: h for h, l in zip(handles, labels)}

wunsch_reihenfolge = [
    'Vollplatte, einachsig tragend, einfach gelagert\n(Standardaufbau)',
    'Vollplatte, einachsig tragend, durchlaufend\n(Standardaufbau)',
    'Mindeststärke für erhöhte\nSchallschutzanforderungen (24 cm)',
    'Vollplatte, zweiachsig tragend, einfach gelagert\n(Standardaufbau)',
    'Vollplatte, zweiachsig tragend, durchlaufend\n(Standardaufbau)',
    'Plattenbalken, einachsig tragend, einfach gelagert\n(Standardaufbau)',
    'Plattenbalken, einachsig tragend, einfach gelagert\n(Standardaufbau), Flanschhöhe'
]


ordered_handles = [unique_dict[l] for l in wunsch_reihenfolge if l in unique_dict]
ordered_labels = [l for l in wunsch_reihenfolge if l in unique_dict]

ax_leg.legend(ordered_handles, ordered_labels, loc="upper center", ncol=3,
              frameon=False, handletextpad=0.5, columnspacing=1.0)

# Speichern
plt.savefig("Strukturhoehe_Systemvergleich.png", dpi=600)
plt.savefig("Strukturhoehe_Systemvergleich.pdf", bbox_inches='tight')
plt.show()