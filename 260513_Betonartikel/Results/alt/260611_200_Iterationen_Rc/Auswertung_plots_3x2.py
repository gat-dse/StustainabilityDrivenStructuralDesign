import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==============================================================================
# DATA LOADING & PREPARATION
# ==============================================================================
excel_file = "260611_1515_Members.xlsx"
df = pd.read_excel(excel_file)

x_achse = 'l_tot [m]'
y_struc_co2 = 'co2 Struktur [kgCO2eq/m2]'
y_floor_co2 = 'co2 Bodenaufbau [kgCO2eq/m2]'
y_struc_h = 'h_QS [m]'
y_total_h = 'h_tot [m]'
y_load_struc = 'Last Struktur [kN/m2]'
y_load_tot = 'Last_tot [kN/m2]'

kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

# Berechnete Spalten & Konvertierung
df['co2 Total_berechnet [kgCO2eq/m2]'] = df[y_struc_co2] + df[y_floor_co2]

# Datentypen erzwingen
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_struc_co2] = pd.to_numeric(df[y_struc_co2], errors='coerce')
df['co2 Total_berechnet [kgCO2eq/m2]'] = pd.to_numeric(df['co2 Total_berechnet [kgCO2eq/m2]'], errors='coerce')
df[y_struc_h] = pd.to_numeric(df[y_struc_h], errors='coerce')
df[y_total_h] = pd.to_numeric(df[y_total_h], errors='coerce')
df[y_load_struc] = pd.to_numeric(df[y_load_struc], errors='coerce')
df[y_load_tot] = pd.to_numeric(df[y_load_tot], errors='coerce')

# ==============================================================================
# UNIFORMES DESIGN-MAPPING (FARBEN, LINIEN, MARKER)
# ==============================================================================
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': '#000000',
    'BeamContinuousSupEl_rc_rec_massiv': '#000000',
    'BeamSimpleSup_rc_rec_Schuettung': '#2ca02c',
    'BeamSimpleSup_rc_rec_massiv': '#2ca02c',
    'BeamSimpleSup_rc_rib_Schuettung': '#9370db',
    'BeamSimpleSup_rc_rib_massiv': '#9370db',
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042',
    'Slab_LL-eingespannt_rc_rec_Schuettung': '#ffa042',
    'Slab_LL-frei_rc_rec_massiv': '#8b0000',
    'Slab_LL-frei_rc_rec_Schuettung': '#8b0000'
}

marker_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': 'o',
    'BeamContinuousSupEl_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rec_Schuettung': 'o',
    'BeamSimpleSup_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rib_Schuettung': 'o',
    'BeamSimpleSup_rc_rib_massiv': 'o',
    'Slab_LL-eingespannt_rc_rec_massiv': '^',
    'Slab_LL-eingespannt_rc_rec_Schuettung': '^',
    'Slab_LL-frei_rc_rec_massiv': '^',
    'Slab_LL-frei_rc_rec_Schuettung': '^'
}

L_WIDTH_GLOBAL = 0.8
M_SIZE_GLOBAL = 4.5


def get_linestyle_and_width(label, bodenaufbau):
    if 'massiv' in str(bodenaufbau).lower():
        return '-', L_WIDTH_GLOBAL
    else:
        return '--', L_WIDTH_GLOBAL


legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': 'Durchlaufträger, Rechteck (+ Schüttung)',
    'BeamContinuousSupEl_rc_rec_massiv': 'Durchlaufträger, Rechteck',
    'BeamSimpleSup_rc_rec_Schuettung': 'Einfeldträger, Rechteck (+ Schüttung)',
    'BeamSimpleSup_rc_rec_massiv': 'Einfeldträger, Rechteck',
    'BeamSimpleSup_rc_rib_Schuettung': 'Einfeldträger, Plattenbalken (+ Schüttung)',
    'BeamSimpleSup_rc_rib_massiv': 'Einfeldträger, Plattenbalken',
    'Slab_LL-eingespannt_rc_rec_Schuettung': 'Platte, eingespannt (+ Schüttung)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Platte, eingespannt',
    'Slab_LL-frei_rc_rec_Schuettung': 'Platte, frei aufliegend (+ Schüttung)',
    'Slab_LL-frei_rc_rec_massiv': 'Platte, frei aufliegend'
}


def apply_clean_grid(ax):
    ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)


# ==============================================================================
# LOOP FÜR BEIDE SPANNWEITEN-RANGES
# ==============================================================================
spannweiten_bereiche = [(3, 8), (3, 12)]

for x_min, x_max in spannweiten_bereiche:

    # Daten für aktuellen Bereich filtern
    pflicht_spalten = [x_achse, kategorie_1, kategorie_2, y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]']
    df_clean = df.dropna(subset=pflicht_spalten).copy()
    df_filtered = df_clean[df_clean[x_achse].between(x_min, x_max)].copy()

    # Aggregieren
    df_grouped = df_filtered.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[
        [y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]', y_struc_h, y_total_h, y_load_struc, y_load_tot]
    ].mean()

    # Layout-Konfiguration
    ziel_werte = [y_struc_h, y_total_h, y_load_struc, y_load_tot, y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]']
    label_mapping = {
        y_struc_h: r"h$_{struc}$ [m]",
        y_total_h: r"h$_{tot}$ [m]",
        y_load_struc: r"Last$_{struc}$ [kN/m$^2$]",
        y_load_tot: r"Last$_{tot}$ [kN/m$^2$]",
        y_struc_co2: r"GWP$_{struc}$ [kg CO$_2$-eq/m$^2$]",
        'co2 Total_berechnet [kgCO2eq/m2]': r"GWP$_{tot}$ [kg CO$_2$-eq/m$^2$]"
    }

    # Figure erstellen
    fig = plt.figure(figsize=(16, 14))
    sns.set_theme(style="whitegrid")

    # GridSpec zur Vermeidung von abgeschnittenen Elementen am unteren Rand
    gs = fig.add_gridspec(nrows=4, ncols=2, height_ratios=[1, 1, 1, 0.35],
                          left=0.07, right=0.96, top=0.92, bottom=0.05,
                          hspace=0.35, wspace=0.18)

    axes_flat = [
        fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])
    ]

    # Daten plotten
    for i, aktueller_y_wert in enumerate(ziel_werte):
        ax = axes_flat[i]

        for label, g in df_grouped.groupby(kategorie_1):
            bodenaufbau = g[kategorie_2].iloc[0]
            farbe = farb_mapping.get(label, '#7f7f7f')
            schoener_name = legend_label_mapping.get(label, label)
            l_style, l_width = get_linestyle_and_width(label, bodenaufbau)
            m_type = marker_mapping.get(label, 'o')

            ax.plot(g[x_achse], g[aktueller_y_wert], marker=m_type, markersize=M_SIZE_GLOBAL,
                    markeredgewidth=0.5, markeredgecolor='black', color=farbe, linestyle=l_style, linewidth=l_width,
                    label=schoener_name)

        ax.set_ylabel(label_mapping.get(aktueller_y_wert, aktueller_y_wert), fontsize=11, fontweight='bold')
        ax.set_xlabel("Spannweite [m]", fontsize=10)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(bottom=0)
        apply_clean_grid(ax)

    # Achsenbereiche paarweise synchronisieren
    ymax_h = max(axes_flat[0].get_ylim()[1], axes_flat[1].get_ylim()[1])
    axes_flat[0].set_ylim(0, ymax_h)
    axes_flat[1].set_ylim(0, ymax_h)

    ymax_last = max(axes_flat[2].get_ylim()[1], axes_flat[3].get_ylim()[1])
    axes_flat[2].set_ylim(0, ymax_last)
    axes_flat[3].set_ylim(0, ymax_last)

    ymax_co2 = max(axes_flat[4].get_ylim()[1], axes_flat[5].get_ylim()[1])
    axes_flat[4].set_ylim(0, ymax_co2)
    axes_flat[5].set_ylim(0, ymax_co2)

    # Globale Legende sortieren und im unteren Bereich verankern
    handles, labels = axes_flat[0].get_legend_handles_labels()
    sorted_legend = sorted(zip(handles, labels), key=lambda t: t[1])
    handles_sorted, labels_sorted = zip(*sorted_legend) if sorted_legend else ([], [])

    ax_leg = fig.add_subplot(gs[3, :])
    ax_leg.axis('off')
    ax_leg.legend(handles_sorted, labels_sorted, title="System-Spezifikation / Querschnitt und Bodenaufbau",
                  loc="upper center", ncol=2, fontsize='small', title_fontsize='medium', frameon=True)

    # Titel vergeben
    fig.suptitle(f"Multikriterien-Analyse für Betonquerschnitte (Spannweiten {x_min}-{x_max}m)",
                 fontsize=16, fontweight='bold', y=0.97)

    # Speichern des jeweiligen Plots
    filename = f"Multikriterien_Analyse_{x_min}-{x_max}m.png"
    plt.savefig(filename, dpi=300)
    print(f"Plot erfolgreich gespeichert unter: {filename}")

    # --- GEWÜNSCHTE ERGÄNZUNG: PLOT ANZEIGEN & RESSOURCEN FREIGEBEN ---
    plt.show()
    plt.close(fig)

print("Alle gewünschten Plots wurden fehlerfrei generiert, angezeigt und gespeichert.")