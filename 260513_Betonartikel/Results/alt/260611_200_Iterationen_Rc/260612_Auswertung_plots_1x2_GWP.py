import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# GLOBALE EINSTELLUNGEN
# ==============================================================================
# Option 1: 'kurz' -> 3 bis 8 m | Option 2: 'lang' -> 3 bis 12 m
SPANNWEITEN_MODUS = 'kurz'

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
pflicht_spalten = [x_achse, kategorie_1, kategorie_2, y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]', y_struc_h, y_total_h]
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

# ==============================================================================
# DESIGN-MAPPINGS
# ==============================================================================
farb_mapping = {
    # Durchlaufträger (Schwarz als Referenz)
    'BeamContinuousSupEl_rc_rec_Schuettung': '#000000',
    'BeamContinuousSupEl_rc_rec_massiv': '#000000',

    # Einfeldträger
    'BeamSimpleSup_rc_rec_Schuettung': '#2ca02c',  # Grün (Rechteck)
    'BeamSimpleSup_rc_rec_massiv': '#2ca02c',
    'BeamSimpleSup_rc_rib_Schuettung': '#9370db',  # Violett (Plattenbalken/Rippe)
    'BeamSimpleSup_rc_rib_massiv': '#9370db',

    # Plattensysteme
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042',  # helleres Orange (Eingespannt)
    'Slab_LL-eingespannt_rc_rec_Schuettung': '#ffa042',
    'Slab_LL-frei_rc_rec_massiv': '#8b0000',  # dunkelrot (Frei aufliegend)
    'Slab_LL-frei_rc_rec_Schuettung': '#8b0000'
}

# Absolut identische Geometrie für alle Linien und Marker
L_WIDTH_GLOBAL = 0.8
M_SIZE_GLOBAL = 4.5

def get_linestyle(bodenaufbau):
    if 'massiv' in str(bodenaufbau).lower():
        return '-'
    else:
        return '--'

def get_marker_type(label):
    if 'Slab' in str(label):
        return '^'
    else:
        return 'o'

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
# FUNKTION 1: ORIGINAL 2x2 KRITERIENMATRIX (HÖHEN & GWP)
# ==============================================================================
def generate_kriterien_matrix(data_subset, system_filter_string, haupt_titel):
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(15, 11), sharex='col', sharey='row')
    sns.set_theme(style="whitegrid")

    ax_h_struc = axes[0, 0]
    ax_h_tot = axes[0, 1]
    ax_gwp_str = axes[1, 0]
    ax_gwp_tot = axes[1, 1]

    df_plot = data_subset[data_subset[kategorie_1].str.contains(system_filter_string)].copy()
    df_plot = df_plot.sort_values(by=[kategorie_1, x_achse])

    system_handles = []

    for label, g in df_plot.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe = farb_mapping.get(label, '#7f7f7f')
        schoener_name = legend_label_mapping.get(label, label)

        l_style = get_linestyle(bodenaufbau)
        m_type = get_marker_type(label)

        # --- 1. h_struc ---
        h_line, = ax_h_struc.plot(g[x_achse], g[y_struc_h], marker=m_type, markersize=M_SIZE_GLOBAL,
                                  markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe,
                                  color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL, label=schoener_name)

        # --- 2. h_tot ---
        ax_h_tot.plot(g[x_achse], g[y_total_h], marker=m_type, markersize=M_SIZE_GLOBAL,
                      markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe,
                      color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL)

        # --- 3. GWP Struktur ---
        ax_gwp_str.plot(g[x_achse], g[y_struc_co2], marker=m_type, markersize=M_SIZE_GLOBAL,
                        markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe,
                        color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL)

        # --- 4. GWP Total ---
        ax_gwp_tot.plot(g[x_achse], g['co2 Total_berechnet [kgCO2eq/m2]'], marker=m_type, markersize=M_SIZE_GLOBAL,
                        markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe,
                        color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL)

        system_handles.append(h_line)

    ax_h_struc.set_title("Höhe Struktur $h_{struc}$", fontsize=12, fontweight='bold', color='#2c3e50', pad=8)
    ax_h_tot.set_title("Gesamthöhe System $h_{total}$", fontsize=12, fontweight='bold', color='#2c3e50', pad=8)
    ax_gwp_str.set_title("GWP Struktur", fontsize=12, fontweight='bold', color='#2c3e50', pad=8)
    ax_gwp_tot.set_title("GWP Total", fontsize=12, fontweight='bold', color='#2c3e50', pad=8)

    ax_h_struc.set_ylabel("Höhe [m]", fontsize=11, fontweight='bold')
    ax_gwp_str.set_ylabel(r"GWP [kg CO$_{2}$-eq / m$^2$]", fontsize=11, fontweight='bold')
    ax_gwp_str.set_xlabel("Spannweite [m]", fontsize=11, fontweight='bold')
    ax_gwp_tot.set_xlabel("Spannweite [m]", fontsize=11, fontweight='bold')

    for ax in [ax_h_struc, ax_h_tot, ax_gwp_str, ax_gwp_tot]:
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(bottom=0)
        ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)

    eindeutige_systeme = dict(zip([h.get_label() for h in system_handles], system_handles))
    sortierte_labels = sorted(eindeutige_systeme.keys())
    sortierte_handles = [eindeutige_systeme[lbl] for lbl in sortierte_labels]

    fig.legend(
        sortierte_handles, sortierte_labels,
        title="Betrachtete Bauteil-Systeme",
        loc='upper center', bbox_to_anchor=(0.5, 0.13), ncol=2, fontsize='small', frameon=True
    )

    voller_titel = f"{haupt_titel} ({x_min}-{x_max}m)"
    fig.suptitle(voller_titel, fontsize=14, fontweight='bold', y=0.97)
    plt.tight_layout(rect=[0, 0.14, 1, 0.94])

    safe_title = haupt_titel.replace(' ', '_')
    filename = f"Kriterienmatrix_{safe_title}_{x_min}-{x_max}m.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Diagramm erfolgreich gespeichert unter: {filename}")


# ==============================================================================
# FUNKTION 2: NEUER GWP SINGLE PLOT (MARKER GEFÜLLT VS. LEER)
# ==============================================================================
def generate_single_gwp_plot(data_subset, system_filter_string, haupt_titel):
    fig, ax = plt.subplots(figsize=(11, 7))
    sns.set_theme(style="whitegrid")

    df_plot = data_subset[data_subset[kategorie_1].str.contains(system_filter_string)].copy()
    df_plot = df_plot.sort_values(by=[kategorie_1, x_achse])

    system_handles = []

    meta_handles = [
        plt.Line2D([0], [0], marker='o', color='gray', markerfacecolor='none', linestyle='-',
                   linewidth=0.8, markeredgecolor='gray', label='GWP Struktur (Marker leer)'),
        plt.Line2D([0], [0], marker='o', color='gray', markerfacecolor='gray', linestyle='-',
                   linewidth=0.8, markeredgecolor='gray', label='GWP Total (Marker gefüllt)')
    ]

    for label, g in df_plot.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe = farb_mapping.get(label, '#7f7f7f')
        schoener_name = legend_label_mapping.get(label, label)

        l_style = get_linestyle(bodenaufbau)
        m_type = get_marker_type(label)

        # --- 1. GWP Struktur (Marker LEER) ---
        ax.plot(g[x_achse], g[y_struc_co2], marker=m_type, markersize=5.0,
                markeredgewidth=1.0, markeredgecolor='black', markerfacecolor='none',
                color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL)

        # --- 2. GWP Total (Marker GEFÜLLT) ---
        h_line, = ax.plot(g[x_achse], g['co2 Total_berechnet [kgCO2eq/m2]'], marker=m_type, markersize=5.0,
                          markeredgewidth=0.5, markeredgecolor='black', markerfacecolor=farbe,
                          color=farbe, linestyle=l_style, linewidth=L_WIDTH_GLOBAL, label=schoener_name)

        system_handles.append(h_line)

    ax.set_ylabel(r"GWP [kg CO$_{2}$-eq / m$^2$]", fontsize=11, fontweight='bold')
    ax.set_xlabel("Spannweite [m]", fontsize=11, fontweight='bold')
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)

    eindeutige_systeme = dict(zip([h.get_label() for h in system_handles], system_handles))
    sortierte_labels = sorted(eindeutige_systeme.keys())
    sortierte_handles = [eindeutige_systeme[lbl] for lbl in sortierte_labels]

    alle_handles = meta_handles + sortierte_handles
    alle_labels = [h.get_label() for h in meta_handles] + sortierte_labels

    ax.legend(
        alle_handles, alle_labels,
        title="Legende & Betrachtete Bauteil-Systeme",
        loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize='small', frameon=True
    )

    voller_titel = f"GWP-Vergleich: {haupt_titel} ({x_min}-{x_max}m)"
    ax.set_title(voller_titel, fontsize=13, fontweight='bold', color='#2c3e50', pad=15)
    plt.tight_layout()

    safe_title = haupt_titel.replace(' ', '_')
    filename = f"GWP_SinglePlot_{safe_title}_{x_min}-{x_max}m.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Diagramm erfolgreich gespeichert unter: {filename}")


# ==============================================================================
# PLOTS AUSFÜHREN (ERZEUGT JETZT BEIDE VARIANTEN)
# ==============================================================================
# 1. Aufruf der ursprünglichen 2x2-Kriterienmatrizen
generate_kriterien_matrix(df_grouped, 'BeamContinuous|BeamSimpleSup', "Einfeldträger vs. Durchlaufträger")
generate_kriterien_matrix(df_grouped, 'BeamContinuous|Slab', "Plattensysteme vs. Durchlaufträger")

# 2. Aufruf der neuen GWP-Single-Plots
generate_single_gwp_plot(df_grouped, 'BeamContinuous|BeamSimpleSup', "Einfeldträger vs. Durchlaufträger")
generate_single_gwp_plot(df_grouped, 'BeamContinuous|Slab', "Plattensysteme vs. Durchlaufträger")

plt.show()