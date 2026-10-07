import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sqlite3
import numpy as np
import pandas as pd
import statistics
import struct_analysis  # file with code for structural analysis
import os

# define database
database_name = "database_260617_Hochbau.db"
#connect to the database
connection = sqlite3.connect(database_name)
# create cursor object
cursor = connection.cursor()
#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C20/25
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C20/25%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC2025 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("C20/25:")
print(dfC2025["PRO_ID"])
print(dfC2025["DENSITY"])
print(dfC2025["Total_GWP"])
print(dfC2025["Total_GWP_m3"])
print(dfC2025["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C25/30
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C25/30%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC2530 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("C25/30:")
print(dfC2530["PRO_ID"])
print(dfC2530["DENSITY"])
print(dfC2530["Total_GWP"])
print(dfC2530["Total_GWP_m3"])
print(dfC2530["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C30/37
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C30/37%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC3037 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("C30/37:")
print(dfC3037["PRO_ID"])
print(dfC3037["DENSITY"])
print(dfC3037["Total_GWP"])
print(dfC3037["Total_GWP_m3"])
print(dfC3037["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for all concrete Hochbau
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND (MECH_PROP LIKE '%C20/25%' OR MECH_PROP LIKE '%C25/30%' OR MECH_PROP LIKE '%C30/37%')
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfHochbaubeton = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("Hochbaubeton:")
print(dfHochbaubeton["PRO_ID"])
print(dfHochbaubeton["DENSITY"])
print(dfHochbaubeton["Total_GWP"])
print(dfHochbaubeton["Total_GWP_m3"])
print(dfHochbaubeton["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL24
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL24%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL24 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("GL24:")
print(dfGL24["PRO_ID"])
print(dfGL24["DENSITY"])
print(dfGL24["Total_GWP"])
print(dfGL24["Total_GWP_m3"])
print(dfGL24["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL28
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL28%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL28 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("GL28:")
print(dfGL28["PRO_ID"])
print(dfGL28["DENSITY"])
print(dfGL28["Total_GWP"])
print(dfGL28["Total_GWP_m3"])
print(dfGL28["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL30
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL30%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL30 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("GL30:")
print(dfGL30["PRO_ID"])
print(dfGL30["DENSITY"])
print(dfGL30["Total_GWP"])
print(dfGL30["Total_GWP_m3"])
print(dfGL30["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL32
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL32%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL32 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("GL32:")
print(dfGL32["PRO_ID"])
print(dfGL32["DENSITY"])
print(dfGL32["Total_GWP"])
print(dfGL32["Total_GWP_m3"])
print(dfGL32["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for all GL (BSH)
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfBSH = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("alle BSH:")
print(dfBSH["PRO_ID"])
print(dfBSH["DENSITY"])
print(dfBSH["Total_GWP"])
print(dfBSH["Total_GWP_m3"])
print(dfBSH["MECH_PROP"])



#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber C24
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND ("PRODUCT_NAME" LIKE '%KVH%' OR "PRODUCT_NAME" LIKE "Balkenschichtholz")
        AND MECH_PROP LIKE '%C24%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfKVHC24 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("alle KVH C24:")
print(dfKVHC24["PRO_ID"])
print(dfKVHC24["DENSITY"])
print(dfKVHC24["Total_GWP"])
print(dfKVHC24["Total_GWP_m3"])
print(dfKVHC24["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for CLT
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "PRODUCT_NAME" LIKE '%CLT%'              
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfCLT = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("CLT:")
print(dfCLT["PRO_ID"])
print(dfCLT["DENSITY"])
print(dfCLT["Total_GWP"])
print(dfCLT["Total_GWP_m3"])
print(dfCLT["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for reinforcing steel B500B
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Steel_reinforcing_bar%'
        AND MECH_PROP LIKE '%B500B%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()
print("B500B:")
dfB500B = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfB500B["PRO_ID"])
print(dfB500B["DENSITY"])
print(dfB500B["Total_GWP"])
print(dfB500B["Total_GWP_m3"])
print(dfB500B["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for reinforcing steel B500B
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Steel_reinforcing_bar%'
        AND "MECH_PROP" NOT LIKE '%B500B%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfRebar = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("alle Bewehrungsstähle:")
print(dfRebar["PRO_ID"])
print(dfRebar["DENSITY"])
print(dfRebar["Total_GWP"])
print(dfRebar["Total_GWP_m3"])
print(dfRebar["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for structural steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Structural_steel_profile%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfSteel = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("alle Baustähle:")
print(dfSteel["PRO_ID"])
print(dfSteel["DENSITY"])
print(dfSteel["Total_GWP"])
print(dfSteel["Total_GWP_m3"])
print(dfSteel["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for prestressing steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE "MATERIAL" LIKE '%prestressing steel%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfPosttension = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])
print("alle Spannstähle:")
print(dfPosttension["PRO_ID"])
print(dfPosttension["DENSITY"])
print(dfPosttension["Total_GWP"])
print(dfPosttension["Total_GWP_m3"])
print(dfPosttension["MECH_PROP"])



#________________________________________________________________________________________________________________________
#           BOTH     PLOTS       TOTAL GWP and TOTAL GWP M3 as 2 x 2 Plot
#________________________________________________________________________________________________________________________



y_positions = {
    "C20/25 (#2)": 15,
    "C25/30 (#8)": 14,
    "C30/37 (#23)": 13,
    "BSP (#9)": 11,
    "KVH (#5)": 10,
    "BSH (#11)": 9,
    "B500B (#9)": 7,
    "andere BSt (#4)": 6,
    "Baustahl (#10)": 4,
    "Spannstahl (#5)": 2,
}
def jitter(y, n):
    return y + np.random.uniform(-0.1, 0.1, n)

def plot_data(ax, x_col):
    # Beton

    ax.scatter(dfC2025[x_col], np.full(len(dfC2025), y_positions["C20/25 (#2)"]), color="lightgreen")
    ax.scatter(dfC2530[x_col], np.full(len(dfC2530), y_positions["C25/30 (#8)"]), color="green")
    ax.scatter(dfC3037[x_col], np.full(len(dfC3037), y_positions["C30/37 (#23)"]), color="darkgreen")
    #plt.scatter(dfC3037[x_col], jitter(y_positions["Hochbaubeton"], len(dfC3037)), color="darkgreen")6

    # Holz
    ax.scatter(dfCLT[x_col], np.full(len(dfCLT), y_positions["BSP (#9)"]), color="red")
    ax.scatter(dfKVHC24[x_col], np.full(len(dfKVHC24), y_positions["KVH (#5)"]), color="darkorange")
    ax.scatter(dfBSH[x_col], np.full(len(dfBSH), y_positions["BSH (#11)"]), color="orange")

    # Bewehrungsstahl
    ax.scatter(dfB500B[x_col], np.full(len(dfB500B), y_positions["B500B (#9)"]), color="lightblue")
    ax.scatter(dfRebar[x_col], np.full(len(dfRebar), y_positions["andere BSt (#4)"]), color="blue")

    #Baustahl
    ax.scatter(dfSteel[x_col], np.full(len(dfSteel), y_positions["Baustahl (#10)"]), color="darkblue")

    #Spannstahl
    ax.scatter(dfPosttension[x_col], np.full(len(dfPosttension), y_positions["Spannstahl (#5)"]), color="grey")


    # Linien
    ax.axhline(12, linestyle="--", color="grey")
    ax.axhline(8, linestyle="--", color="grey")
    ax.axhline(5, linestyle="--", color="grey")
    ax.axhline(3, linestyle="--", color="grey")

    ax.grid(axis="x", linestyle=":", alpha=0.5)

plt.rcParams["font.family"] = "Times New Roman"

plt.rcParams.update({
    "font.size": 14
})


# -----------------------
# Figure 2x2
# -----------------------
fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharey=False,gridspec_kw={"height_ratios": [3, 1, 1]})



# -----------------------
# Achsenbeschriftung
# -----------------------
for ax in axes.flatten():
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))


# -----------------------
# OBEN LINKS
# -----------------------
plot_data(axes[0, 0], "Total_GWP")
#axes[0, 0].set_title("Total GWP [kg CO₂-eq / t]")
#axes[0, 0].set_ylabel("Material")
axes[0, 0].set_xlabel("Total GWP [kg CO₂-eq / t]")
axes[0, 0].set_xlim(0, 3000)
axes[0, 0].set_ylim(0, 15.5)

# -----------------------
# OBEN RECHTS
# -----------------------
plot_data(axes[0, 1], "Total_GWP_m3")
#axes[0, 1].set_title("Total GWP [kg CO₂-eq / m³]")
axes[0, 1].set_xlabel("Total GWP [kg CO₂-eq / m³]")
axes[0, 1].set_xlim(0, 30000)
axes[0, 1].set_ylim(0, 15.5)

# -----------------------
# Mitte LINKS zoom Beton
# -----------------------
plot_data(axes[1, 0], "Total_GWP")
axes[1, 0].set_xlim(0, 130)
axes[1, 0].set_ylim(12.5, 15.5)
axes[1, 0].set_xlabel("Total GWP [kg CO₂-eq / t]")

# -----------------------
# Mitte RECHTS zoom Beton
# -----------------------
plot_data(axes[1, 1], "Total_GWP_m3")
axes[1, 1].set_xlim(0, 350)
axes[1, 1].set_ylim(12.5, 15.5)
axes[1, 1].set_xlabel("Total GWP [kg CO₂-eq / m³]")

# -----------------------
# Unten LINKS zoom Holz
# -----------------------
plot_data(axes[2, 0], "Total_GWP")
axes[2, 0].set_xlim(0, 500)
axes[2, 0].set_ylim(8.5, 12)
axes[2, 0].set_xlabel("Total GWP [kg CO₂-eq / t]")

# -----------------------
# unten RECHTS zoom Holz
# -----------------------
plot_data(axes[2, 1], "Total_GWP_m3")
axes[2, 1].set_xlim(0, 280)
axes[2, 1].set_ylim(8.5, 12)
axes[2, 1].set_xlabel("Total GWP [kg CO₂-eq / m³]")


def add_label(ax, label):
    ax.text(
        -0.08, 1.02, label,
        transform=ax.transAxes,
        fontsize=14,
    )

add_label(axes[0, 0], "a)")
add_label(axes[0, 1], "b)")
add_label(axes[1, 0], "c)")
add_label(axes[1, 1], "d)")
add_label(axes[2, 0], "e)")
add_label(axes[2, 1], "f)")

# Box um Ergebnisse:
def add_box(ax, x_min, x_max, y_min, y_max, color, lw=1.5):
    rect = Rectangle(
        (x_min, y_min),
        x_max - x_min,
        y_max - y_min,
        linewidth=lw,
        edgecolor=color,
        facecolor='none',
        linestyle=':'
    )
    ax.add_patch(rect)

ax = axes[0, 0]

# Beton
add_box(ax, 1, 150, 12.5, 15.3, "black")

ax.text(
    200, 14,          # x, y → Position (leicht rechts vom Rahmen)
    "siehe c)",
    fontsize=12,
    color="black",
    va="center"
)

# Holz
add_box(ax, 1, 650, 8.5, 11.8, "black")
ax.text(
    700, 10,          # x, y → Position (leicht rechts vom Rahmen)
    "siehe e)",
    fontsize=12,
    color="black",
    va="center"
)

ax = axes[0, 1]

add_box(ax, 10, 800, 12.5, 15.3, "black")
ax.text(
    1200, 14,          # x, y → Position (leicht rechts vom Rahmen)
    "siehe d)",
    fontsize=12,
    color="black",
    va="center"
)
add_box(ax, 10, 1200, 8.5, 11.8, "black")
ax.text(
    2000, 10,          # x, y → Position (leicht rechts vom Rahmen)
    "siehe f)",
    fontsize=12,
    color="black",
    va="center"
)
"""
ax = axes[1, 0]
add_box(ax, 2, 129, 12.6, 15.4, "green")


ax = axes[1, 1]
add_box(ax, 5, 345, 12.6, 15.4, "green")


ax = axes[2, 0]
add_box(ax, 5, 495, 8.6, 11.9, "red")


ax = axes[2, 1]
add_box(ax, 5, 275, 8.6, 11.9, "red")
"""

# -----------------------
# Layout
# -----------------------
plt.tight_layout()

# Dateiname
filename = "GWP_plot"

# Speicherung als PDF (vektorbasiert → perfekt für Paper)
plt.savefig(f"{filename}.pdf",
            bbox_inches="tight",
            dpi=300)

# Speicherung als JPG (für Bericht / Präsentation)
plt.savefig(f"{filename}.jpg",
            bbox_inches="tight",
            dpi=300)

plt.show()



print("Anzahl EPDs pro Datensatz:")

print(f"C20/25: {len(dfC2025)}")
print(f"C25/30: {len(dfC2530)}")
print(f"C30/37: {len(dfC3037)}")
print(f"Hochbaubeton: {len(dfHochbaubeton)}")

print(f"GL24: {len(dfGL24)}")
print(f"GL28: {len(dfGL28)}")
print(f"GL30: {len(dfGL30)}")
print(f"GL32: {len(dfGL32)}")
print(f"BSH (alle): {len(dfBSH)}")

print(f"KVH C24: {len(dfKVHC24)}")
print(f"CLT / BSP: {len(dfCLT)}")

print(f"B500B: {len(dfB500B)}")
print(f"Bewehrungsstahl gesamt: {len(dfRebar)}")

print(f"Baustahl: {len(dfSteel)}")

print(f"Spannstahl: {len(dfPosttension)}")