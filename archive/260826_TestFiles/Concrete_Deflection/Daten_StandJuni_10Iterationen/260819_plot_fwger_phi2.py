"""
Liest die transponierte Sheet2-Datenbank ein und stellt fuer jeden Member den
Faktor fwger(phi=2)_calc dar.
X-Achse: Globaler Member-Index (1..60), jeder Member nur einmal
Kategorisierung: Spannweite l_tot in [4, 6, 8, 10, 12] m, je ein Subplot (Small Multiples).
"""
import sqlite3

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

db_file = "260603_Members_rc_rec_2_10Iterationen_Sheet2.db"
table_name = "members"

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
con = sqlite3.connect(db_file)
df = pd.read_sql(f'SELECT Member_ID, l_tot, "fwger(phi=2)_calc", w_use, w_use_ger FROM {table_name}', con)
con.close()

for col in ["l_tot", "fwger(phi=2)_calc", "w_use", "w_use_ger"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["l_tot", "fwger(phi=2)_calc", "w_use", "w_use_ger"])

spannweiten = [4, 6, 8, 10, 12]

# Globaler, eindeutiger Index je Member (1..60), abgeleitet aus Member_ID
df["member_index"] = df["Member_ID"].str.extract(r"(\d+)").astype(int)

# Bereich, in dem die gerissene Durchbiegung kleiner ist als die ungerissene
df["ger_kleiner_als_use"] = df["w_use_ger"] < df["w_use"]

# ==============================================================================
# DESIGN
# ==============================================================================
farbe_fwger = "#0072B2"
farbe_grenzwert = "#595959"
farbe_hinterlegung = "#f4a9a9"  # Hinterlegung: w_use_ger < w_use
grenzwert = 3.0


def shade_condition_regions(ax, x_vals, condition, color, alpha=0.6):
    """Hinterlegt zusammenhaengende x-Bereiche, in denen 'condition' True ist."""
    x_vals = list(x_vals)
    condition = list(condition)
    n = len(x_vals)
    i = 0
    while i < n:
        if condition[i]:
            j = i
            while j + 1 < n and condition[j + 1]:
                j += 1
            step_left = (x_vals[i] - x_vals[i - 1]) if i > 0 else (x_vals[1] - x_vals[0] if n > 1 else 1)
            step_right = (x_vals[j + 1] - x_vals[j]) if j + 1 < n else (x_vals[j] - x_vals[j - 1] if j > 0 else 1)
            left = x_vals[i] - step_left / 2
            right = x_vals[j] + step_right / 2
            ax.axvspan(left, right, color=color, alpha=alpha, zorder=0, linewidth=0)
            i = j + 1
        else:
            i += 1


# ==============================================================================
# PLOT: SMALL MULTIPLES, EIN SUBPLOT JE SPANNWEITE
# ==============================================================================
fig, axes = plt.subplots(1, len(spannweiten), figsize=(4 * len(spannweiten), 5), sharey=True)

for ax, l in zip(axes, spannweiten):
    df_l = df[df["l_tot"] == l].sort_values("member_index")
    shade_condition_regions(ax, df_l["member_index"], df_l["ger_kleiner_als_use"], farbe_hinterlegung)
    ax.plot(df_l["member_index"], df_l["fwger(phi=2)_calc"], marker="o", markersize=6,
            linewidth=2, color=farbe_fwger, label="fwger(phi=2)_calc")
    ax.axhline(y=grenzwert, color=farbe_grenzwert, linestyle="--", linewidth=1.5,
               label=f"f(x) = {grenzwert}")
    ax.set_title(f"l_tot = {l} m")
    ax.set_xlabel("Member Nr. (1–60)")
    ax.set_xticks(df_l["member_index"])
    ax.grid(True, linewidth=0.5, alpha=0.4)

axes[0].set_ylabel("fwger (phi=2) [-]")

handles, labels = axes[0].get_legend_handles_labels()
handles.append(Patch(facecolor=farbe_hinterlegung, alpha=0.6, label="w_use_ger < w_use"))
labels.append("w_use_ger < w_use")
fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.05))

fig.suptitle("Faktor fwger(phi=2)_calc je Member, kategorisiert nach Spannweite")
fig.tight_layout(rect=[0, 0.03, 1, 1])

fig.savefig("260819_fwger_phi2.png", dpi=300, bbox_inches="tight")
fig.savefig("260819_fwger_phi2.pdf", bbox_inches="tight")
print("Diagramm gespeichert: 260819_fwger_phi2.png / .pdf")

plt.show()
