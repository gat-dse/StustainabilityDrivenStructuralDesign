"""
Liest die Members_rc_rec_simple_massiv-Datenbank ein und stellt co2 in Abhaengigkeit
der Spannweite l_tot dar - alle Beton-/Bewehrungs-Produktkombinationen in EINEM Diagramm.

Die Spannweite ist die physikalische, stetige Groesse und liegt daher auf der X-Achse.
Die Produkt-ID (prod_id_concrete) ist lediglich ein Bezeichner fuer einen Datensatz aus
der Hintergrunddatenbank (kein geometrischer/stetiger Wert) und wird daher kategorial
ueber die Linienfarbe codiert (6 feste Farben, keine numerische Achse).
prod_id_rebar (103 / 109) wird zusaetzlich ueber den Linienstil codiert.
"""
import sqlite3

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

db_file = "Members_rc_rec_simple_massiv.db"
table_name = "members"

mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 14
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['xtick.labelsize'] = 14
mpl.rcParams['ytick.labelsize'] = 14
mpl.rcParams['legend.fontsize'] = 11

# ==============================================================================
# DATA LOADING & PREPARATION
# ==============================================================================
con = sqlite3.connect(db_file)
df = pd.read_sql(f"SELECT Member_ID, l_tot, prod_id_concrete, prod_id_rebar, co2 FROM {table_name}", con)
con.close()

for col in ["l_tot", "prod_id_concrete", "prod_id_rebar", "co2"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["l_tot", "prod_id_concrete", "prod_id_rebar", "co2"])

concrete_prod_ids = sorted(df["prod_id_concrete"].unique())
rebar_prod_ids = [103, 109]
linien_stil = {103: "-", 109: "--"}

# ==============================================================================
# DESIGN: kategoriale Farben (fixe Reihenfolge, keine numerische Skala) je Beton-Produkt-ID
# ==============================================================================
kategorial_farben = ["#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7"]
farb_mapping = dict(zip(concrete_prod_ids, kategorial_farben))

# ==============================================================================
# PLOT: EIN DIAGRAMM, SPANNWEITE AUF DER X-ACHSE
# ==============================================================================
fig, ax = plt.subplots(figsize=(10, 7))

for prod_c in concrete_prod_ids:
    farbe = farb_mapping[prod_c]
    for prod_r in rebar_prod_ids:
        df_sub = df[(df["prod_id_concrete"] == prod_c) & (df["prod_id_rebar"] == prod_r)].sort_values("l_tot")
        ax.plot(df_sub["l_tot"], df_sub["co2"], marker="o", markersize=6, markeredgecolor="white",
                markeredgewidth=0.6, linewidth=2, color=farbe, linestyle=linien_stil[prod_r])

ax.set_xlabel("Spannweite l_tot [m]")
ax.set_ylabel("co2 [kgCO2eq/m²]")
ax.set_xticks(sorted(df["l_tot"].unique()))
ax.grid(True, linewidth=0.5, alpha=0.4)
ax.set_title("co2 vs. Spannweite, je Beton- und Bewehrungs-Produkt\n"
             "(Members_rc_rec_simple_massiv)")

# Kategoriale Farb-Legende (Beton-Produkt-ID)
farb_legende = [Line2D([0], [0], color=farb_mapping[pc], linewidth=2, marker="o",
                        label=f"prod_id_concrete = {int(pc)}") for pc in concrete_prod_ids]
legende_1 = ax.legend(handles=farb_legende, loc="upper left", title="Beton-Produkt")
ax.add_artist(legende_1)

# Separate Legende fuer den Linienstil (Bewehrungs-Produkt-ID)
linienstil_legende = [
    Line2D([0], [0], color="black", linestyle=linien_stil[103], label="prod_id_rebar = 103"),
    Line2D([0], [0], color="black", linestyle=linien_stil[109], label="prod_id_rebar = 109"),
]
ax.legend(handles=linienstil_legende, loc="lower right", title="Bewehrungs-Produkt")

fig.tight_layout()

fig.savefig("SimpleMassiv_co2_vs_span.png", dpi=300, bbox_inches="tight")
fig.savefig("SimpleMassiv_co2_vs_span.pdf", bbox_inches="tight")
print("Diagramm gespeichert: SimpleMassiv_co2_vs_span.png / .pdf")

plt.show()
