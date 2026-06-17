import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==============================================================================
# GLOBALE EINSTELLUNGEN
# ==============================================================================
SPANNWEITEN_MODUS = 'lang'  # 'kurz' -> 3 bis 8 m | 'lang' -> 3 bis 12 m
excel_file = "260611_1515_Members.xlsx"

# ==============================================================================
# DATA LOADING & PREPARATION
# ==============================================================================
df = pd.read_excel(excel_file)

x_achse = 'l_tot [m]'
y_struc_co2 = 'co2 Struktur [kgCO2eq/m2]'
y_floor_co2 = 'co2 Bodenaufbau [kgCO2eq/m2]'
y_struc_h = 'h_QS [m]'
y_total_h = 'h_tot [m]'

kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

# GWP Total berechnen
df['co2 Total_berechnet [kgCO2eq/m2]'] = df[y_struc_co2] + df[y_floor_co2]

# Datentypen erzwingen
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_struc_co2] = pd.to_numeric(df[y_struc_co2], errors='coerce')
df['co2 Total_berechnet [kgCO2eq/m2]'] = pd.to_numeric(df['co2 Total_berechnet [kgCO2eq/m2]'], errors='coerce')
df[y_struc_h] = pd.to_numeric(df[y_struc_h], errors='coerce')
df[y_total_h] = pd.to_numeric(df[y_total_h], errors='coerce')

# Bereinigen
pflicht_spalten = [x_achse, kategorie_1, kategorie_2, y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]', y_struc_h,
                   y_total_h]
df_clean = df.dropna(subset=pflicht_spalten).copy()

if SPANNWEITEN_MODUS == 'lang':
    x_min, x_max = 3, 12
else:
    x_min, x_max = 3, 8

df_filtered = df_clean[df_clean[x_achse].between(x_min, x_max)]

# Mittelwerte aggregieren
df_grouped = df_filtered.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[[
    y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]', y_struc_h, y_total_h
]].mean()

# Dynamische Limits für identische Y-Skalierung ermitteln
max_hoehe = max(df_grouped[y_struc_h].max(), df_grouped[y_total_h].max()) * 1.1
max_gwp = max(df_grouped[y_struc_co2].max(), df_grouped['co2 Total_berechnet [kgCO2eq/m2]'].max()) * 1.1

# ==============================================================================
# DESIGN-MAPPINGS
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

L_WIDTH_GLOBAL = 0.8
M_SIZE_GLOBAL = 5.5


def get_linestyle(bodenaufbau):
    return '-' if 'massiv' in str(bodenaufbau).lower() else '--'


def get_marker_type(label):
    return '^' if 'Slab' in str(label) else 'o'


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


# ==============================================================================
# HILFSFUNKTION FÜR DESIGN & REINES ACHSEN-LAYOUT
# ==============================================================================
def setup_clean_axes(axes_matrix, y_max, y_label_text):
    """ Konfiguriert die Achsen so, dass Textüberschneidungen unmöglich sind """
    ax_top_str, ax_top_tot = axes_matrix[0, 0], axes_matrix[0, 1]
    ax_bot_str, ax_bot_tot = axes_matrix[1, 0], axes_matrix[1, 1]

    # Nur die linken Plots bekommen die Y-Achsenbeschriftung
    ax_top_str.set_ylabel(y_label_text, fontsize=11, fontweight='bold')
    ax_bot_str.set_ylabel(y_label_text, fontsize=11, fontweight='bold')

    # Nur die unteren Plots bekommen die X-Achsenbeschriftung
    ax_bot_str.set_xlabel("Spannweite [m]", fontsize=11, fontweight='bold')
    ax_bot_tot.set_xlabel("Spannweite [m]", fontsize=11, fontweight='bold')

    for ax in [ax_top_str, ax_top_tot, ax_bot_str, ax_bot_tot]:
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(0, y_max)
        ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)


# ==============================================================================
# 1. GENERATOR FÜR KOMBINIERTE HÖHENMATRIX
# ==============================================================================
def generate_combined_height_matrix(data_subset):
    fig = plt.figure(figsize=(15, 12))

    # GridSpec teilt das Layout mathematisch exakt auf:
    # hspace (Abstand Vertikal) und wspace (Abstand Horizontal) sind fest fixiert.
    gs = fig.add_gridspec(nrows=3, ncols=2, height_ratios=[1, 1, 0.2],
                          left=0.08, right=0.96, top=0.90, bottom=0.05,
                          hspace=0.32, wspace=0.18)

    # Subplots an die GridSpec-Positionen binden (inkl. echtem Sharing der Achsen)
    ax_top_str = fig.add_subplot(gs[0, 0])
    ax_top_tot = fig.add_subplot(gs[0, 1], sharex=ax_top_str, sharey=ax_top_str)
    ax_bot_str = fig.add_subplot(gs[1, 0], sharex=ax_top_str, sharey=ax_top_str)
    ax_bot_tot = fig.add_subplot(gs[1, 1], sharex=ax_top_str, sharey=ax_top_str)

    axes_matrix = np.array([[ax_top_str, ax_top_tot], [ax_bot_str, ax_bot_tot]])

    filter_top = 'BeamContinuous|BeamSimpleSup'
    filter_bot = 'BeamContinuous|Slab'
    all_handles, all_labels = [], []

    # --- REIHE 1: Einfeldträger vs. Durchlaufträger ---
    df_top = data_subset[data_subset[kategorie_1].str.contains(filter_top)].copy().sort_values(
        by=[kategorie_1, x_achse])
    for label, g in df_top.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe, l_style, m_type = farb_mapping.get(label, '#7f7f7f'), get_linestyle(bodenaufbau), get_marker_type(label)
        schoener_name = legend_label_mapping.get(label, label)

        ax_top_str.plot(g[x_achse], g[y_struc_h], marker=m_type, markersize=M_SIZE_GLOBAL, markeredgewidth=0.5,
                        markeredgecolor='black', markerfacecolor=farbe, color=farbe, linestyle=l_style,
                        linewidth=L_WIDTH_GLOBAL)
        h_line, = ax_top_tot.plot(g[x_achse], g[y_total_h], marker=m_type, markersize=M_SIZE_GLOBAL,
                                  markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe, color=farbe,
                                  linestyle=l_style, linewidth=L_WIDTH_GLOBAL)
        all_handles.append(h_line)
        all_labels.append(schoener_name)

    # --- REIHE 2: Plattensysteme vs. Durchlaufträger ---
    df_bot = data_subset[data_subset[kategorie_1].str.contains(filter_bot)].copy().sort_values(
        by=[kategorie_1, x_achse])
    for label, g in df_bot.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe, l_style, m_type = farb_mapping.get(label, '#7f7f7f'), get_linestyle(bodenaufbau), get_marker_type(label)
        schoener_name = legend_label_mapping.get(label, label)

        ax_bot_str.plot(g[x_achse], g[y_struc_h], marker=m_type, markersize=M_SIZE_GLOBAL, markeredgewidth=0.5,
                        markeredgecolor='black', markerfacecolor=farbe, color=farbe, linestyle=l_style,
                        linewidth=L_WIDTH_GLOBAL)
        h_line, = ax_bot_tot.plot(g[x_achse], g[y_total_h], marker=m_type, markersize=M_SIZE_GLOBAL,
                                  markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe, color=farbe,
                                  linestyle=l_style, linewidth=L_WIDTH_GLOBAL)
        all_handles.append(h_line)
        all_labels.append(schoener_name)

    # Titel vergeben
    ax_top_str.set_title("Einfeldträger vs. Durchlaufträger\nHöhe Struktur $h_{struc}$", fontsize=11, fontweight='bold',
                         color='#2c3e50', pad=10)
    ax_top_tot.set_title("Einfeldträger vs. Durchlaufträger\nGesamthöhe System $h_{total}$", fontsize=11,
                         fontweight='bold', color='#2c3e50', pad=10)
    ax_bot_str.set_title("Plattensysteme vs. Durchlaufträger\nHöhe Struktur $h_{struc}$", fontsize=11,
                         fontweight='bold', color='#2c3e50', pad=10)
    ax_bot_tot.set_title("Plattensysteme vs. Durchlaufträger\nGesamthöhe System $h_{total}$", fontsize=11,
                         fontweight='bold', color='#2c3e50', pad=10)

    # Achsen einrichten
    setup_clean_axes(axes_matrix, max_hoehe, "Höhe [m]")

    # Globale Figure-Überschrift ganz oben verankern
    fig.suptitle(f"Kombinierte Höhenmatrix (Globale Skalierung, Spannweite {x_min}-{x_max}m)", fontsize=13,
                 fontweight='bold', y=0.96)

    # Legende exakt in Reihe 3 (über beide Spalten gemerged) platzieren
    eindeutige = dict(zip(all_labels, all_handles))
    ax_leg = fig.add_subplot(gs[2, :])
    ax_leg.axis('off')
    ax_leg.legend([eindeutige[k] for k in sorted(eindeutige.keys())], sorted(eindeutige.keys()),
                  title="Betrachtete Bauteil-Systeme", title_fontsize='medium',
                  loc='center', ncol=2, fontsize='small', frameon=True)

    filename = f"Kombination_Hoehen_Matrizen_{SPANNWEITEN_MODUS}_{x_min}-{x_max}m.png"
    plt.savefig(filename, dpi=300)  # Kein tight_layout mehr nötig, da GridSpec perfekt fixiert ist
    print(f"Kombiniertes Höhen-Diagramm erfolgreich gespeichert unter: {filename}")


# ==============================================================================
# 2. GENERATOR FÜR KOMBINIERTE GWP MATRIX
# ==============================================================================
def generate_combined_gwp_plot(data_subset):
    fig = plt.figure(figsize=(15, 12))

    gs = fig.add_gridspec(nrows=3, ncols=2, height_ratios=[1, 1, 0.2],
                          left=0.08, right=0.96, top=0.90, bottom=0.05,
                          hspace=0.32, wspace=0.18)

    ax_top_str = fig.add_subplot(gs[0, 0])
    ax_top_tot = fig.add_subplot(gs[0, 1], sharex=ax_top_str, sharey=ax_top_str)
    ax_bot_str = fig.add_subplot(gs[1, 0], sharex=ax_top_str, sharey=ax_top_str)
    ax_bot_tot = fig.add_subplot(gs[1, 1], sharex=ax_top_str, sharey=ax_top_str)

    axes_matrix = np.array([[ax_top_str, ax_top_tot], [ax_bot_str, ax_bot_tot]])

    filter_top = 'BeamContinuous|BeamSimpleSup'
    filter_bot = 'BeamContinuous|Slab'
    all_handles, all_labels = [], []

    # --- REIHE 1: Einfeldträger vs. Durchlaufträger ---
    df_top = data_subset[data_subset[kategorie_1].str.contains(filter_top)].copy().sort_values(
        by=[kategorie_1, x_achse])
    for label, g in df_top.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe, l_style, m_type = farb_mapping.get(label, '#7f7f7f'), get_linestyle(bodenaufbau), get_marker_type(label)
        schoener_name = legend_label_mapping.get(label, label)

        ax_top_str.plot(g[x_achse], g[y_struc_co2], marker=m_type, markersize=M_SIZE_GLOBAL, markeredgewidth=0.5,
                        markeredgecolor='black', markerfacecolor=farbe, color=farbe, linestyle=l_style,
                        linewidth=L_WIDTH_GLOBAL)
        h_line, = ax_top_tot.plot(g[x_achse], g['co2 Total_berechnet [kgCO2eq/m2]'], marker=m_type,
                                  markersize=M_SIZE_GLOBAL, markeredgewidth=0.5, markeredgecolor='black',
                                  markerfacecolor=farbe, color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL)
        all_handles.append(h_line)
        all_labels.append(schoener_name)

    # --- REIHE 2: Plattensysteme vs. Durchlaufträger ---
    df_bot = data_subset[data_subset[kategorie_1].str.contains(filter_bot)].copy().sort_values(
        by=[kategorie_1, x_achse])
    for label, g in df_bot.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe, l_style, m_type = farb_mapping.get(label, '#7f7f7f'), get_linestyle(bodenaufbau), get_marker_type(label)
        schoener_name = legend_label_mapping.get(label, label)

        ax_bot_str.plot(g[x_achse], g[y_struc_co2], marker=m_type, markersize=M_SIZE_GLOBAL, markeredgewidth=0.5,
                        markeredgecolor='black', markerfacecolor=farbe, color=farbe, linestyle=l_style,
                        linewidth=L_WIDTH_GLOBAL)
        h_line, = ax_bot_tot.plot(g[x_achse], g['co2 Total_berechnet [kgCO2eq/m2]'], marker=m_type,
                                  markersize=M_SIZE_GLOBAL, markeredgewidth=0.5, markeredgecolor='black',
                                  markerfacecolor=farbe, color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL)
        all_handles.append(h_line)
        all_labels.append(schoener_name)

    # Titel vergeben
    ax_top_str.set_title("Einfeldträger vs. Durchlaufträger\nGWP Struktur", fontsize=11, fontweight='bold',
                         color='#2c3e50', pad=10)
    ax_top_tot.set_title("Einfeldträger vs. Durchlaufträger\nGWP Total", fontsize=11, fontweight='bold',
                         color='#2c3e50', pad=10)
    ax_bot_str.set_title("Plattensysteme vs. Durchlaufträger\nGWP Struktur", fontsize=11, fontweight='bold',
                         color='#2c3e50', pad=10)
    ax_bot_tot.set_title("Plattensysteme vs. Durchlaufträger\nGWP Total", fontsize=11, fontweight='bold',
                         color='#2c3e50', pad=10)

    # Achsen einrichten
    setup_clean_axes(axes_matrix, max_gwp, r"GWP [kg CO$_{2}$-eq / m$^2$]")

    # Globale Figure-Überschrift
    fig.suptitle(f"Kombinierte GWP-Matrix (Globale Skalierung, Spannweite {x_min}-{x_max}m)", fontsize=13,
                 fontweight='bold', y=0.96)

    # Legende exakt in Reihe 3 platzieren
    eindeutige = dict(zip(all_labels, all_handles))
    ax_leg = fig.add_subplot(gs[2, :])
    ax_leg.axis('off')
    ax_leg.legend([eindeutige[k] for k in sorted(eindeutige.keys())], sorted(eindeutige.keys()),
                  title="Betrachtete Bauteil-Systeme", title_fontsize='medium',
                  loc='center', ncol=2, fontsize='small', frameon=True)

    filename = f"Kombination_GWP_Matrizen_{SPANNWEITEN_MODUS}_{x_min}-{x_max}m.png"
    plt.savefig(filename, dpi=300)
    print(f"Kombiniertes GWP-Diagramm erfolgreich gespeichert unter: {filename}")


# ==============================================================================
# EXECUTION
# ==============================================================================
generate_combined_height_matrix(df_grouped)
generate_combined_gwp_plot(df_grouped)
plt.show()