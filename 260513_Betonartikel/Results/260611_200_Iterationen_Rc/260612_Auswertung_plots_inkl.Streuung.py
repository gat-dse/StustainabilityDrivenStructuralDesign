import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib as mpl

# ==============================================================================
# GLOBALE EINSTELLUNGEN & DATENPREPARATION
# ==============================================================================
excel_file = "260611_1515_Members.xlsx"
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
y_struc_co2 = 'co2 Struktur [kgCO2eq/m2]'
kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

# Datentypen erzwingen
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_struc_co2] = pd.to_numeric(df[y_struc_co2], errors='coerce')

# Bereinigen & Filtern: Spannweite 3 bis 12 m & NUR massiver Bodenaufbau
pflicht_spalten = [x_achse, kategorie_1, kategorie_2, y_struc_co2]
df_clean = df.dropna(subset=pflicht_spalten).copy()

df_filtered = df_clean[
    (df_clean[x_achse].between(3, 12)) &
    (df_clean[kategorie_2].str.lower() == 'massiv')
    ].copy()

# ==============================================================================
# UNIFORMES DESIGN-MAPPING (FARBEN & MARKER)
# ==============================================================================
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': '#000000',  # Schwarz als Referenz
    'BeamSimpleSup_rc_rec_massiv': '#2ca02c',  # Grün (Rechteck)
    'BeamSimpleSup_rc_rib_massiv': '#9370db',  # Violett (Plattenbalken)
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042',  # Orange (Eingespannt)
    'Slab_LL-frei_rc_rec_massiv': '#8b0000'  # Dunkelrot (Frei)
}

marker_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rib_massiv': 'o',
    'Slab_LL-eingespannt_rc_rec_massiv': '^',
    'Slab_LL-frei_rc_rec_massiv': '^'
}

legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'Plattenstreifen, eingespannt\n(Standardaufbau)',
    'BeamSimpleSup_rc_rec_massiv': 'Plattenstreifen, frei aufgelegt\n(Standardaufbau)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Platte liniengelagert, eingespannt\n(Standardaufbau)',
    'Slab_LL-frei_rc_rec_massiv': 'Platte liniengelagert, frei aufgelegt\n(Standardaufbau)',
    'BeamSimpleSup_rc_rib_massiv': 'Plattenbalken, frei aufgelegt\n(Standardaufbau)'
    }

L_WIDTH_GLOBAL = 1.0
M_SIZE_GLOBAL = 4.0


def apply_clean_grid(ax):
    ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)


# Aggregation für die Kennwerte der Streuung (Mittelwert, Minimum, Maximum)
df_band = df_filtered.groupby([x_achse, kategorie_1], as_index=False)[y_struc_co2].agg(['mean', 'min', 'max'])


# ==============================================================================
# PLOT-FUNKTION MIT LEGENDE UNTERHALB
# ==============================================================================
def generate_streuung_plot(filter_keywords, title_text, filename):
    # Erhöhte Figure-Höhe für den Legendenplatz unten
    fig = plt.figure(figsize=(12, 9))

    # GridSpec: Zeile 0 für das Diagramm, Zeile 1 exklusiv für die Legende
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1, 0.15],
                          left=0.10, right=0.95, top=0.90, bottom=0.05, hspace=0.3)

    ax = fig.add_subplot(gs[0])
    ax_leg = fig.add_subplot(gs[1])
    ax_leg.axis('off')  # Keine Achsenlinien im Legenden-Feld

    # Filtere die relevanten Systeme für diesen Plot heraus
    df_plot = df_band[df_band[kategorie_1].str.contains(filter_keywords)].copy()
    df_plot = df_plot.sort_values(by=[kategorie_1, x_achse])

    for label, g in df_plot.groupby(kategorie_1):
        farbe = farb_mapping.get(label, '#7f7f7f')
        schoener_name = legend_label_mapping.get(label, label)
        marker_style = marker_mapping.get(label, 'o')

        # 1. Streuung als helle Fläche
        ax.fill_between(g[x_achse], g['min'], g['max'], color=farbe, alpha=0.12, label='_nolegend_')

        # 2. Mittelwert-Linie
        ax.plot(g[x_achse], g['mean'], marker=marker_style, markersize=M_SIZE_GLOBAL,
                markeredgewidth=0.5, markeredgecolor='black', color=farbe,
                linestyle='-', linewidth=L_WIDTH_GLOBAL, label=schoener_name)

    ax.set_xlim(3, 12)
    ax.set_ylim(bottom=0)
    ax.set_title(title_text, pad=15)
    ax.set_xlabel("Spannweite [m]")
    ax.set_ylabel(r"GWP$_{structure}$ [kg CO$_{2eq}$ / m$^2$]")

    apply_clean_grid(ax)

    # Legende im unteren Slot zentrieren (mehrspaltig falls nötig)
    handles, labels = ax.get_legend_handles_labels()
    ax_leg.legend(handles, labels,
                  loc="upper center", ncol=3, frameon=False)

    # Speichern und Schließen
    plt.savefig(filename, dpi=600)
    # Speichern als PDF (für die wissenschaftliche Arbeit / Vektor-Qualität)
    plt.savefig(f"{filename}.pdf", bbox_inches='tight')

    print(f"Plot erfolgreich gespeichert unter: {filename}")


# ==============================================================================
# PLOTS GENERIEREN
# ==============================================================================

# Plot 1: 1D-Systeme (Einfeldträger & Durchlaufträger)
generate_streuung_plot(
    filter_keywords='BeamSimpleSup|BeamContinuous',
    title_text="GWP Struktur inkl. Datenstreuung für 1D-Systeme (Bodenaufbau Standard)",
    filename="GWP_Struktur_1D_Systeme_Streuung.png"
)

# Plot 2: 2D-Systeme (Platten & Durchlaufträger als Referenz)
generate_streuung_plot(
    filter_keywords='Slab|BeamContinuous',
    title_text="GWP Struktur inkl. Datenstreuung für 2D-Systeme & Referenz (Bodenaufbau Standard)",
    filename="GWP_Struktur_2D_Systeme_Streuung.png"
)

# Plot 3: Alle Systeme (Platten & Durchlaufträger als Referenz)
generate_streuung_plot(
    filter_keywords='Slab|Beam',
    title_text="GWP Struktur inkl. Datenstreuung für 2D-Systeme & Referenz (Bodenaufbau Standard)",
    filename="GWP_Struktur_Alle_Systeme_Streuung.png"
)


# Plots anzeigen
plt.show()