"""
Liest die Members_rc_rec_simple_massiv-Datenbank ein und stellt den Bewehrungsgehalt roh
in Abhaengigkeit des GWP-Verhaeltnisses Bewehrung/Beton (gwp_rebar / gwp_concrete) dar.

X-Achse: GWP-Verhaeltnis Stahl/Beton (stetige, physikalische/oekonomische Groesse).
Je x-Position ist die zugehoerige Produktkombination (Beton-/Bewehrungs-Produkt-ID)
als Achsenbeschriftung angegeben (statischer Ersatz fuer eine Hover-Beschriftung).
Kategorisierung: Spannweite l_tot in [3..12] m, je ein Subplot (Small Multiples) MIT
unabhaengiger y-Skalierung, da die Variation von roh je Spannweite sehr klein ist.
"""
import sqlite3

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

db_file = "Members_rc_rec_simple_massiv.db"
table_name = "members"

mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 14
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['xtick.labelsize'] = 11
mpl.rcParams['ytick.labelsize'] = 12
mpl.rcParams['legend.fontsize'] = 12
mpl.rcParams['axes.formatter.useoffset'] = False

# ==============================================================================
# DATA LOADING & PREPARATION
# ==============================================================================
con = sqlite3.connect(db_file)
df = pd.read_sql(
    f"SELECT Member_ID, l_tot, roh, prod_id_concrete, prod_id_rebar, gwp_concrete, gwp_rebar "
    f"FROM {table_name}", con)
con.close()

for col in ["l_tot", "roh", "prod_id_concrete", "prod_id_rebar", "gwp_concrete", "gwp_rebar"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["l_tot", "roh", "prod_id_concrete", "prod_id_rebar", "gwp_concrete", "gwp_rebar"])

# GWP-Verhaeltnis Stahl/Beton: stetige, physikalisch/oekonomisch sinnvolle Groesse
df["gwp_ratio"] = df["gwp_rebar"] / df["gwp_concrete"]

# Produkt-Label je x-Position (Ersatz fuer Hover-Beschriftung)
df["produkt_label"] = ("c" + df["prod_id_concrete"].astype(int).astype(str)
                        + "/r" + df["prod_id_rebar"].astype(int).astype(str))

spannweiten = sorted(df["l_tot"].unique())

# Feste, gleichmaessig verteilte x-Positionen in der Reihenfolge des GWP-Verhaeltnisses:
# Die 12 Produktkombinationen liegen teils sehr nah beieinander (z.B. 5.07 / 5.23 / 5.26 / 5.44),
# echte (ungleichmaessige) Abstaende wuerden die Beschriftungen unlesbar machen. Da roh ohnehin
# nicht stetig mit dem Verhaeltnis zusammenhaengt (siehe Zickzack-Verlauf), ist eine gleichmaessige
# kategoriale Anordnung, sortiert nach dem Verhaeltnis, hier sinnvoller.
achsen_referenz = df[df["l_tot"] == spannweiten[0]].sort_values("gwp_ratio").reset_index(drop=True)
rang_mapping = {row["produkt_label"]: i for i, row in achsen_referenz.iterrows()}
df["gwp_rang"] = df["produkt_label"].map(rang_mapping)

x_ticks = list(rang_mapping.values())
x_labels = [f"{row['produkt_label']}  ({row['gwp_ratio']:.1f})" for _, row in achsen_referenz.iterrows()]

# ==============================================================================
# DESIGN
# ==============================================================================
farbe_roh = "#0072B2"

# ==============================================================================
# PLOT: SMALL MULTIPLES, EIN SUBPLOT JE SPANNWEITE, UNABHAENGIGE Y-SKALIERUNG
# ==============================================================================
fig, axes = plt.subplots(1, len(spannweiten), figsize=(5.2 * len(spannweiten), 6.5), sharex=True)

for ax, l in zip(axes, spannweiten):
    df_l = df[df["l_tot"] == l].sort_values("gwp_rang")
    ax.plot(df_l["gwp_rang"], df_l["roh"], marker="o", markersize=6, linewidth=2, color=farbe_roh)
    ax.set_title(f"l_tot = {l} m")
    ax.grid(True, linewidth=0.5, alpha=0.4)

axes[0].set_ylabel("roh (unten) [-]")
axes[len(axes) // 2].set_xlabel("GWP-Verhältnis Stahl/Beton (aufsteigend sortiert, gleichmäßig verteilt)\n"
                                 "— Beschriftung je Punkt: Verhältniswert / Beton-Produkt-ID / Bewehrungs-Produkt-ID")

# Gemeinsame x-Achsenbeschriftung (Produktkombination) fuer alle Subplots, da x-Positionen identisch sind
for ax in axes:
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, rotation=90)

fig.suptitle("Bewehrungsgehalt roh vs. GWP-Verhältnis Stahl/Beton, je Spannweite\n"
             "(Members_rc_rec_simple_massiv; y-Achse je Spannweite unabhängig skaliert)")
fig.tight_layout(rect=[0, 0, 1, 0.95])

fig.savefig("SimpleMassiv_roh_vs_gwp_ratio.png", dpi=300, bbox_inches="tight")
fig.savefig("SimpleMassiv_roh_vs_gwp_ratio.pdf", bbox_inches="tight")
print("Diagramm gespeichert: SimpleMassiv_roh_vs_gwp_ratio.png / .pdf")

plt.show()
