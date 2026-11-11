import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# ==============================================================================
# GLOBALE EINSTELLUNGEN & DATENPREPARATION
# ==============================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_file = os.path.join(script_dir, "260625_1654_Members.xlsx")
Sprache = 'de' #Wahl Sprache: 'en' oder 'de'


df = pd.read_excel(excel_file)

mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 14
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['xtick.labelsize'] = 14
mpl.rcParams['ytick.labelsize'] = 14
mpl.rcParams['legend.fontsize'] = 14

x_achse = 'l_tot [m]'
y_struc_h = 'h_QS [m]'
y_struc_co2 = 'co2 Struktur [kgCO2eq/m2]'
kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

# Datentypen erzwingen
for spalte in [x_achse, y_struc_h, y_struc_co2, 'h_f [m]']:
    df[spalte] = pd.to_numeric(df[spalte], errors='coerce')

# Bereinigen & Filtern: Spannweite 3 bis 12 m & NUR massiver Bodenaufbau
def filtern(pflicht_spalten):
    df_clean = df.dropna(subset=pflicht_spalten).copy()
    return df_clean[
        (df_clean[x_achse].between(3, 12)) &
        (df_clean[kategorie_2].str.lower() == 'massiv')
    ].copy()

# Höhe: Mittelwerte inkl. Flanschhöhe
df_h = filtern([x_achse, kategorie_1, kategorie_2, y_struc_h])
df_h = df_h.groupby([x_achse, kategorie_1], as_index=False)[[y_struc_h, 'h_f [m]']].mean()
df_h = df_h.sort_values(by=[kategorie_1, x_achse])

# GWP: Mittelwert, Minimum, Maximum (Streuung)
df_co2 = filtern([x_achse, kategorie_1, kategorie_2, y_struc_co2])
df_co2 = df_co2.groupby([x_achse, kategorie_1], as_index=False)[y_struc_co2].agg(['mean', 'min', 'max'])
df_co2 = df_co2.sort_values(by=[kategorie_1, x_achse])

# ==============================================================================
# DESIGN-MAPPINGS (für beide Diagramme identisch, damit eine Legende genügt)
# ==============================================================================
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': '#000000',
    'BeamSimpleSup_rc_rec_massiv': '#2ca02c',
    'BeamSimpleSup_rc_rib_massiv': '#9370db',
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042',
    'Slab_LL-frei_rc_rec_massiv': '#8b0000'
}
farbe_flansch = '#b57edc'  # Lavendel: gleicher Farbton wie Rippenplatte (#9370db), heller, aber kräftiger als #d8bfd8

marker_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rib_massiv': 'o',
    'Slab_LL-eingespannt_rc_rec_massiv': '^',
    'Slab_LL-frei_rc_rec_massiv': '^'
}

legend_label_mapping_EN = {
    'BeamContinuousSupEl_rc_rec_massiv': 'Solid slab, single-axis load-bearing,\ncontinuous (standard superstructure)',
    'BeamSimpleSup_rc_rec_massiv': 'Solid slab, single-axis load-bearing,\nsimply supported (standard superstructure)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Solid slab, two-axis load-bearing,\ncontinuous (standard superstructure)',
    'Slab_LL-frei_rc_rec_massiv': 'Solid slab, two-axis load-bearing,\nsimply supported (standard superstructure)',
    'BeamSimpleSup_rc_rib_massiv': 'Ribbed plate, single-axis load-bearing,\nsimply supported,\n(standard superstructure)'
}

legend_label_mapping_DE = {
    'BeamContinuousSupEl_rc_rec_massiv': 'Vollplatte, einachsig tragend, durchlaufend\n(Standardaufbau)',
    'BeamSimpleSup_rc_rec_massiv': 'Vollplatte, einachsig tragend, einfach gelagert\n(Standardaufbau)',
    'BeamSimpleSup_rc_rib_massiv': 'Rippenplatte, einachsig tragend, einfach gelagert\n(Standardaufbau)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Vollplatte, zweiachsig tragend, durchlaufend\n(Standardaufbau)',
    'Slab_LL-frei_rc_rec_massiv': 'Vollplatte, zweiachsig tragend, einfach gelagert\n(Standardaufbau)',
}

if Sprache == 'en':
    legend_label_mapping = legend_label_mapping_EN
    label_flansch = 'Ribbed plate, single-axis load-bearing,\nsimply supported,\n(standard superstructure), flange height'
    label_schall = 'construction height to meet higher\nsound insulation requirements (24 cm)'
    xlabel = "Span [m]"
elif Sprache == 'de':
    legend_label_mapping = legend_label_mapping_DE
    label_flansch = 'Rippenplatte, einachsig tragend, einfach gelagert\n(Standardaufbau), Flanschhöhe'
    label_schall = 'Mindeststärke für erhöhte\nSchallschutzanforderungen (24 cm)'
    xlabel = "Spannweite [m]"

L_WIDTH_GLOBAL = 1.0
M_SIZE_GLOBAL = 4.0


def apply_clean_grid(ax):
    ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)
    ax.set_axisbelow(True)


# ==============================================================================
# FIGURE: ZWEI DIAGRAMME NEBENEINANDER + GEMEINSAME LEGENDE UNTEN
# Figure-Grösse, Achsenpositionen, Legende und Titel wie 260729_Auswertung_plots_1x2_GWP.py,
# damit Diagramme und Schrift im Artikel bei gleicher Bildbreite gleich gross erscheinen.
# ==============================================================================
fig, (ax_h, ax_co2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

# --- Links: Höhe Struktur ---
for label, g in df_h.groupby(kategorie_1):
    farbe = farb_mapping.get(label, '#7f7f7f')
    ax_h.plot(g[x_achse], g[y_struc_h], marker=marker_mapping.get(label, 'o'), markersize=M_SIZE_GLOBAL,
              markeredgewidth=0.5, markeredgecolor='black', color=farbe,
              linestyle='-', linewidth=L_WIDTH_GLOBAL, label=legend_label_mapping.get(label, label))

    # Flanschhöhe für Plattenbalken
    if 'rib' in label:
        ax_h.plot(g[x_achse], g['h_f [m]'], color=farbe_flansch,
                  linestyle='-.', linewidth=1.5, label=label_flansch)

# Schallschutz-Referenz
h_schallschutz = 0.24
ax_h.axhline(y=h_schallschutz, color='#d32f2f', linestyle='--', linewidth=1.2, label=label_schall)

ax_h.set_ylabel("$h_{structure}$ [m]")

# --- Rechts: GWP Struktur inkl. Streuung ---
for label, g in df_co2.groupby(kategorie_1):
    farbe = farb_mapping.get(label, '#7f7f7f')
    # Streuung als helle Fläche
    ax_co2.fill_between(g[x_achse], g['min'], g['max'], color=farbe, alpha=0.12, label='_nolegend_')
    # Mittelwert-Linie
    ax_co2.plot(g[x_achse], g['mean'], marker=marker_mapping.get(label, 'o'), markersize=M_SIZE_GLOBAL,
                markeredgewidth=0.5, markeredgecolor='black', color=farbe,
                linestyle='-', linewidth=L_WIDTH_GLOBAL, label=legend_label_mapping.get(label, label))

ax_co2.set_ylabel("GWP$_{structure}$ [kg CO$_{2}$-eq / m$^2$]")

# --- Gemeinsames Achsen-Design ---
for ax, lbl in zip((ax_h, ax_co2), ['a)', 'b)']):
    ax.text(-0.01, 1.02, lbl, transform=ax.transAxes, va='bottom', ha='right', clip_on=False)
    ax.set_xlim(3, 12)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(xlabel)
    apply_clean_grid(ax)

# ==============================================================================
# GEMEINSAME LEGENDE (Dubletten entfernen & sortieren)
# ==============================================================================
unique_dict = {}
for ax in (ax_co2, ax_h):  # Höhe zuletzt -> deren Handles haben Vorrang
    handles, labels = ax.get_legend_handles_labels()
    unique_dict.update({l: h for h, l in zip(handles, labels)})

wunsch_reihenfolge = [
    legend_label_mapping['BeamSimpleSup_rc_rec_massiv'],
    legend_label_mapping['BeamContinuousSupEl_rc_rec_massiv'],
    label_schall,
    legend_label_mapping['Slab_LL-frei_rc_rec_massiv'],
    legend_label_mapping['Slab_LL-eingespannt_rc_rec_massiv'],
    legend_label_mapping['BeamSimpleSup_rc_rib_massiv'],
    label_flansch,
]

ordered_handles = [unique_dict[l] for l in wunsch_reihenfolge if l in unique_dict]
ordered_labels = [l for l in wunsch_reihenfolge if l in unique_dict]

# Achsenpositionen fix wie in 260729_Auswertung_plots_1x2_GWP.py (dort Resultat von tight_layout),
# damit Diagrammgrösse und Abstand exakt gleich sind
fig.subplots_adjust(left=0.0764, right=0.9744, bottom=0.2405, top=0.7975, wspace=0.2078)

# Legende exakt so breit wie im Referenzplot (13.304 in, x = -0.652 ... 12.652 in);
# da die Legende breiter als die Figure ist, bestimmt sie die Bildbreite beim Speichern
# (mode='expand' zieht links und rechts je borderaxespad = 0.5 * Schriftgrösse ab -> hier wieder addiert)
leg_pad = 0.5 * mpl.rcParams['legend.fontsize'] / 72
leg_x0, leg_breite = (-0.652 - leg_pad) / 12, (13.304 + 2 * leg_pad) / 12
fig.legend(ordered_handles, ordered_labels, loc='upper center', bbox_to_anchor=(leg_x0, 0.08, leg_breite, 0),
           mode='expand', ncol=3, frameon=False)
'''
if Sprache == 'en':
    haupt_titel = "Structural height and GWP"
elif Sprache == 'de':
    haupt_titel = "Höhe und GWP Struktur"
fig.suptitle(f"{haupt_titel} (3-12m)", y=0.98)'''

# Speichern
filenamepng = os.path.join(script_dir, f"Strukturhoehe_und_GWP_Systemvergleich_{Sprache}.png")
filenamepdf = os.path.splitext(filenamepng)[0] + ".pdf"
plt.savefig(filenamepng, dpi=600, bbox_inches='tight')
plt.savefig(filenamepdf, bbox_inches='tight')
print(f"Plot erfolgreich gespeichert unter: {filenamepng} und {filenamepdf}")
plt.show()
