import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# ==============================================================================
# GLOBALE EINSTELLUNGEN
# ==============================================================================
SPANNWEITEN_MODUS = 'lang'
excel_file = "260611_1515_Members.xlsx"

mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 14
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['xtick.labelsize'] = 14
mpl.rcParams['ytick.labelsize'] = 14
mpl.rcParams['legend.fontsize'] = 14

# ==============================================================================
# DATA LOADING & PREPARATION
# ==============================================================================
df = pd.read_excel(excel_file)
x_achse = 'l_tot [m]'
y_struc_co2 = 'co2 Struktur [kgCO2eq/m2]'
y_floor_co2 = 'co2 Bodenaufbau [kgCO2eq/m2]'
#y_struc_h = 'h_QS [m]'
#y_total_h = 'h_tot [m]'
kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

df['co2 Total_berechnet [kgCO2eq/m2]'] = df[y_struc_co2] + df[y_floor_co2]

df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_struc_co2] = pd.to_numeric(df[y_struc_co2], errors='coerce')
df['co2 Total_berechnet [kgCO2eq/m2]'] = pd.to_numeric(df['co2 Total_berechnet [kgCO2eq/m2]'], errors='coerce')
#df[y_struc_h] = pd.to_numeric(df[y_struc_h], errors='coerce')
#df[y_total_h] = pd.to_numeric(df[y_total_h], errors='coerce')

df_clean = df.dropna(
    subset=[x_achse, kategorie_1, kategorie_2, y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]',
            #y_struc_h, y_total_h
            ]).copy()

x_min, x_max = (3, 12) if SPANNWEITEN_MODUS == 'lang' else (3, 8)
df_filtered = df_clean[df_clean[x_achse].between(x_min, x_max)]
df_grouped = df_filtered.groupby([x_achse, kategorie_1, kategorie_2], as_index=False)[[
    y_struc_co2, 'co2 Total_berechnet [kgCO2eq/m2]', #y_struc_h, y_total_h
]].mean()

# ==============================================================================
# DESIGN-MAPPINGS
# ==============================================================================
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_Schuettung': '#000000', 'BeamContinuousSupEl_rc_rec_massiv': '#000000',
    'BeamSimpleSup_rc_rec_Schuettung': '#2ca02c', 'BeamSimpleSup_rc_rec_massiv': '#2ca02c',
    'BeamSimpleSup_rc_rib_Schuettung': '#9370db', 'BeamSimpleSup_rc_rib_massiv': '#9370db',
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042', 'Slab_LL-eingespannt_rc_rec_Schuettung': '#ffa042',
    'Slab_LL-frei_rc_rec_massiv': '#8b0000', 'Slab_LL-frei_rc_rec_Schuettung': '#8b0000'
}


def get_linestyle(bodenaufbau): return '-' if 'massiv' in str(bodenaufbau).lower() else '--'
def get_marker_type(label): return '^' if 'Slab' in str(label) else 'o'


legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'Plattenstreifen, eingespannt\n(Standardaufbau)',
    'BeamContinuousSupEl_rc_rec_Schuettung': 'Plattenstreifen, eingespannt\n(Standardaufbau + Schüttung)',
    'BeamSimpleSup_rc_rec_massiv': 'Plattenstreifen, frei aufgelegt\n(Standardaufbau)',
    'BeamSimpleSup_rc_rec_Schuettung': 'Plattenstreifen, frei aufgelegt\n(Standardaufbau + Schüttung)',
    'BeamSimpleSup_rc_rib_massiv': 'Plattenbalken, frei aufgelegt\n(Standardaufbau)',
    'BeamSimpleSup_rc_rib_Schuettung': 'Plattenbalken, frei aufgelegt\n(Standardaufbau + Schüttung)',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Platte liniengelagert, eingespannt\n(Standardaufbau)',
    'Slab_LL-eingespannt_rc_rec_Schuettung': 'Platte liniengelagert, eingespannt\n(Standardaufbau + Schüttung)',
    'Slab_LL-frei_rc_rec_massiv': 'Platte liniengelagert, frei aufgelegt\n(Standardaufbau)',
    'Slab_LL-frei_rc_rec_Schuettung': 'Platte liniengelagert, frei aufgelegt\n(Standardaufbau + Schüttung)'
}


# ==============================================================================
# SUBPLOT GENERATOR
# ==============================================================================
def generate_kriterien_matrix(data_subset, system_filter_string, haupt_titel):
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6), sharex='col', sharey='row')
    ax_list = [axes[0], axes[1]]

    df_plot = data_subset[data_subset[kategorie_1].str.contains(system_filter_string)].copy()
    system_handles = {}

    for label, g in df_plot.groupby(kategorie_1):
        bodenaufbau = g[kategorie_2].iloc[0]
        farbe = farb_mapping.get(label, '#7f7f7f')
        l_s, m_t = get_linestyle(bodenaufbau), get_marker_type(label)
        leg_text = legend_label_mapping.get(label, label)

        h, = axes[0].plot(g[x_achse], g[y_struc_co2], marker=m_t, markersize=4, markeredgewidth=0.5,
                             markeredgecolor='black', color=farbe, linestyle=l_s, label=leg_text)
        axes[1].plot(g[x_achse], g['co2 Total_berechnet [kgCO2eq/m2]'], marker=m_t, markersize=4, markeredgewidth=0.5,
                        markeredgecolor='black', color=farbe, linestyle=l_s)
        system_handles[leg_text] = h

    for ax, lbl in zip(ax_list, ['a)', 'b)', 'c)', 'd)']):
        ax.text(-0.01, 1.02, lbl, transform=ax.transAxes, va='bottom', ha='right', clip_on=False)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(bottom=0)
        ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)
        ax.set_axisbelow(True)
        ax.tick_params(axis='both', which='major', labelsize=14, labelbottom=True, labelleft=True)

    axes[0].set_ylabel("GWP$_{structure}$ [kg CO$_{2}$-eq / m$^2$]")
    axes[1].set_ylabel("GWP$_{total}$ [kg CO$_{2}$-eq / m$^2$]")
    axes[0].set_xlabel("Spannweite [m]")
    axes[1].set_xlabel("Spannweite [m]")

    desired_order = list(legend_label_mapping.values())
    ordered_labels = [l for l in desired_order if l in system_handles]
    ordered_handles = [system_handles[l] for l in ordered_labels]

    fig.legend(ordered_handles, ordered_labels, loc='upper center', bbox_to_anchor=(0.5, 0.08), ncol=3, frameon=False)
    fig.suptitle(f"{haupt_titel} ({x_min}-{x_max}m)", y=0.98)
    plt.tight_layout(rect=[0, 0.12, 1, 0.95])

    filename = f"GWP_Matrix_{haupt_titel.replace(' ', '_')}_{x_min}-{x_max}m.png"
    plt.savefig(filename, dpi=600, bbox_inches='tight')
    # Speichern als PDF (für die wissenschaftliche Arbeit / Vektor-Qualität)
    plt.savefig(f"{filename}.pdf", bbox_inches='tight')
    print(f"Gespeichert unter: {filename}")


generate_kriterien_matrix(df_grouped, 'BeamContinuous|BeamSimpleSup', "Einfeldträger vs. Durchlaufträger")
generate_kriterien_matrix(df_grouped, 'BeamContinuous|Slab', "Plattensysteme vs. Durchlaufträger")
plt.show()