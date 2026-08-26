"""
Kombiniert alle vier Einzeldiagramme (w_use/w_use_ger, fwger(phi=2)_calc, roh/rohs, h/d_calc)
fuer Members_rc_rib_simple_massiv in einer Uebersichtsgrafik:
4 Zeilen (je eine Kenngroesse) x 10 Spalten (je eine Spannweite von 3 bis 12 m).
X-Achse je Spalte: Globaler Member-Index (1..120), jeder Member nur einmal.
Hinterlegung (hellrot) in allen Zeilen: Bereich, in dem w_use_ger < w_use.
"""
import sqlite3

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

db_file = "Members_rc_rib_simple_massiv.db"
table_name = "members"

mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 13
mpl.rcParams['axes.labelsize'] = 13
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 11
mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['axes.formatter.useoffset'] = False

# ==============================================================================
# DATA LOADING & PREPARATION
# ==============================================================================
con = sqlite3.connect(db_file)
df = pd.read_sql(
    f'SELECT Member_ID, l_tot, w_use, w_use_ger, "fwger(phi=2)_calc", roh, rohs, "h/d_calc" FROM {table_name}',
    con)
con.close()

value_cols = ["l_tot", "w_use", "w_use_ger", "fwger(phi=2)_calc", "roh", "rohs", "h/d_calc"]
for col in value_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=value_cols)

spannweiten = list(range(3, 13))

# Globaler, eindeutiger Index je Member (1..120), abgeleitet aus Member_ID
df["member_index"] = df["Member_ID"].str.extract(r"(\d+)").astype(int)

# Bereich, in dem die gerissene Durchbiegung kleiner ist als die ungerissene
df["ger_kleiner_als_use"] = df["w_use_ger"] < df["w_use"]

# ==============================================================================
# DESIGN
# ==============================================================================
farbe_1 = "#0072B2"
farbe_2 = "#D55E00"
farbe_grenzwert = "#595959"
farbe_hinterlegung = "#f4a9a9"  # Hinterlegung: w_use_ger < w_use


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
# ZEILEN-DEFINITION: je Kenngroesse eine Zeile
# ==============================================================================
zeilen = [
    {"cols": ["w_use", "w_use_ger"], "colors": [farbe_1, farbe_2],
     "labels": ["w_use (ungerissen)", "w_use_ger (gerissen)"],
     "ylabel": "Durchbiegung w [m]", "grenzwert": None},
    {"cols": ["fwger(phi=2)_calc"], "colors": [farbe_1],
     "labels": ["fwger(phi=2)_calc"],
     "ylabel": "fwger (phi=2) [-]", "grenzwert": 3.0},
    {"cols": ["roh", "rohs"], "colors": [farbe_1, farbe_2],
     "labels": ["roh (unten)", "rohs (oben)"],
     "ylabel": "Bewehrungsgehalt [-]", "grenzwert": None},
    {"cols": ["h/d_calc"], "colors": [farbe_1],
     "labels": ["h/d_calc"],
     "ylabel": "h/d [-]", "grenzwert": None},
]

# ==============================================================================
# PLOT: 4 ZEILEN (KENNGROESSEN) x 10 SPALTEN (SPANNWEITEN)
# ==============================================================================
fig, axes = plt.subplots(len(zeilen), len(spannweiten), figsize=(2.6 * len(spannweiten), 3.6 * len(zeilen)),
                          sharex="col")

for row_idx, zeile in enumerate(zeilen):
    for col_idx, l in enumerate(spannweiten):
        ax = axes[row_idx, col_idx]
        df_l = df[df["l_tot"] == l].sort_values("member_index")
        shade_condition_regions(ax, df_l["member_index"], df_l["ger_kleiner_als_use"], farbe_hinterlegung)

        for col_name, color, label in zip(zeile["cols"], zeile["colors"], zeile["labels"]):
            ax.plot(df_l["member_index"], df_l[col_name], marker="o", markersize=4,
                    linewidth=1.6, color=color, label=label)

        if zeile["grenzwert"] is not None:
            ax.axhline(y=zeile["grenzwert"], color=farbe_grenzwert, linestyle="--", linewidth=1.2,
                       label=f"f(x) = {zeile['grenzwert']}")

        ax.grid(True, linewidth=0.5, alpha=0.4)
        ax.set_xticks(df_l["member_index"])
        ax.tick_params(axis="x", labelrotation=90)

        if row_idx == 0:
            ax.set_title(f"l_tot = {l} m")
        if row_idx == len(zeilen) - 1:
            ax.set_xlabel("Member Nr.")
        if col_idx == 0:
            ax.set_ylabel(zeile["ylabel"])
            ax.legend(loc="best", framealpha=0.9, fontsize=9)

# Figuren-weite Legende nur fuer die Hinterlegung (Bedeutung ist in allen Zeilen identisch)
fig.legend(handles=[Patch(facecolor=farbe_hinterlegung, alpha=0.6, label="w_use_ger < w_use")],
           loc="lower center", bbox_to_anchor=(0.5, -0.01))

fig.suptitle("Uebersicht: Durchbiegung, fwger(phi=2), Bewehrungsgehalt und h/d je Member, "
             "kategorisiert nach Spannweite\n(Members_rc_rib_simple_massiv)", fontsize=16)
fig.tight_layout(rect=[0, 0.02, 1, 0.96])

fig.savefig("Rib_combined_overview.pdf", bbox_inches="tight")
fig.savefig("Rib_combined_overview.png", dpi=300, bbox_inches="tight")
print("Diagramm gespeichert: Rib_combined_overview.pdf / .png")

plt.show()
