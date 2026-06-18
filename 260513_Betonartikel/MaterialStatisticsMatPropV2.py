import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
plt.rcParams["font.family"] = "Times New Roman"
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


#________________________________________________________________________________________________________________
#             TEIL 2: eigenschaftsspezifische Emissionen
#________________________________________________________________________________________________________________

#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C20/25
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C20/25%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC2025 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
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
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C25/30%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC2530 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
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
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C30/37%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC3037 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("C30/37:")
print(dfC3037["PRO_ID"])
print(dfC3037["DENSITY"])
print(dfC3037["Total_GWP"])
print(dfC3037["Total_GWP_m3"])
print(dfC3037["MECH_PROP"])



#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL24
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL24%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL24 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
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
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL28%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL28 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
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
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL30%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL30 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
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
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL32%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL32 = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("GL32:")
print(dfGL32["PRO_ID"])
print(dfGL32["DENSITY"])
print(dfGL32["Total_GWP"])
print(dfGL32["Total_GWP_m3"])
print(dfGL32["MECH_PROP"])



#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber C24
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND ("PRODUCT_NAME" LIKE '%KVH%' OR "PRODUCT_NAME" LIKE "Balkenschichtholz")
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfKVH = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("alle KVH:")
print(dfKVH["PRO_ID"])
print(dfKVH["DENSITY"])
print(dfKVH["Total_GWP"])
print(dfKVH["Total_GWP_m3"])
print(dfKVH["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for CLT
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "PRODUCT_NAME" LIKE '%CLT%'              
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfCLT = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("CLT:")
print(dfCLT["PRO_ID"])
print(dfCLT["DENSITY"])
print(dfCLT["Total_GWP"])
print(dfCLT["Total_GWP_m3"])
print(dfCLT["MECH_PROP"])



#------------------------------------------------------------------------------------------------------------------------
#extract values for reinforcing steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Steel_reinforcing_bar%'
        AND "MECH_PROP" NOT LIKE '%B500B%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfRebar = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("Bewehrungsstahl ihne B500B:")
print(dfRebar["PRO_ID"])
print(dfRebar["DENSITY"])
print(dfRebar["Total_GWP"])
print(dfRebar["Total_GWP_m3"])
print(dfRebar["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for reinforcing steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Steel_reinforcing_bar%'
        AND MECH_PROP LIKE '%B500B%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfB500B = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("B500B:")
print(dfB500B["PRO_ID"])
print(dfB500B["DENSITY"])
print(dfB500B["Total_GWP"])
print(dfB500B["Total_GWP_m3"])
print(dfB500B["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for structural steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Structural_steel_profile%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfSteel = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("alle Baustähle:")
print(dfSteel["PRO_ID"])
print(dfSteel["DENSITY"])
print(dfSteel["Total_GWP"])
print(dfSteel["Total_GWP_m3"])
print(dfSteel["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for posttensioning steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME, ID, "Copy for strength" FROM products
        WHERE "MATERIAL" LIKE '%prestressing steel%'
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfPosttension = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
print("alle Baustähle:")
print(dfPosttension["PRO_ID"])
print(dfPosttension["DENSITY"])
print(dfPosttension["Total_GWP"])
print(dfPosttension["Total_GWP_m3"])
print(dfPosttension["MECH_PROP"])

#_______________________________________________________________________________________________________________________
#_______________________________________________________________________________________________________________________
#_______________________________________________________________________________________________________________________


# alle DataFrames sammeln
dfs = [
    dfC2025, dfC2530, dfC3037,
    dfGL24, dfGL28, dfGL30, dfGL32,
    dfKVH, dfCLT,
    dfRebar,dfB500B, dfSteel, dfPosttension
]

# MECH_PROP zusammenziehen
all_mech_props = pd.concat([df["MECH_PROP"] for df in dfs])

# Unique Werte (ohne NaN)
all_mech_props = all_mech_props.dropna().unique()

# ausgeben
print("Alle MECH_PROP:")
for mech in all_mech_props:
    print(mech)

"""
inquiry = ("SELECT strength_bend, strength_comp, strength_tens, E_modulus, density_load,fmd, ftd, fcd FROM material_prop WHERE"
           " name=" + mech_prop)
cursor.execute(inquiry)
result = cursor.fetchall()
fmk, fck, ftk, Emmean, weight, fmd, ftd, fcd = result[0]
"""

# alle materialeigenschaften sammeln

query = """
SELECT name, strength_bend, strength_comp, strength_tens,
       E_modulus, density_load, fmd, ftd, fcd
FROM material_prop
"""
df_mat = pd.read_sql_query(query, connection)

# namen vereinheitlichen
df_mat = df_mat.rename(columns={
    "name": "MECH_PROP"
})


# Liste der betroffenen Materialien
target = ["C20/25", "C25/30", "C30/37"]

df_mat.loc[df_mat["MECH_PROP"].isin(target), "ftd"] = 0


#mergen
def add_material_properties(df, df_mat):
    return df.merge(df_mat, on="MECH_PROP", how="left")



dfC2025 = add_material_properties(dfC2025, df_mat)
dfC2530 = add_material_properties(dfC2530, df_mat)
dfC3037 = add_material_properties(dfC3037, df_mat)
print("check merge1")
print(dfC3037["PRO_ID"])
print(dfC3037["MECH_PROP"])

dfGL24 = add_material_properties(dfGL24, df_mat)
dfGL28 = add_material_properties(dfGL28, df_mat)
dfGL30 = add_material_properties(dfGL30, df_mat)
dfGL32 = add_material_properties(dfGL32, df_mat)
print("check merge1 dfCLT")
print(dfCLT["PRO_ID"])
print(dfCLT["MECH_PROP"])
dfKVH = add_material_properties(dfKVH, df_mat)
dfCLT = add_material_properties(dfCLT, df_mat)

print("check merge2 dfCLT")
print(dfCLT["PRO_ID"])
print(dfCLT["MECH_PROP"])
print(dfCLT["fcd"])

dfRebar = add_material_properties(dfRebar, df_mat)
dfB500B = add_material_properties(dfB500B, df_mat)

dfSteel = add_material_properties(dfSteel, df_mat)

dfPosttension = add_material_properties(dfPosttension, df_mat)

print("check merge2 dfPosttension")
print(dfPosttension["PRO_ID"])
print(dfPosttension["MECH_PROP"])
print(dfPosttension["fcd"])

# ----------------------------------------
# Normierte Werte berechnen
# ----------------------------------------
dfs_all = [
    dfC2025, dfC2530, dfC3037,
    dfGL24, dfGL28, dfGL30, dfGL32,
    dfKVH, dfCLT, dfB500B,
    dfRebar, dfSteel, dfPosttension
]

for df in dfs_all:
    df["GWP_fcd"] = df["Total_GWP"] / df["fcd"]
    df["GWP_ftd"] = df["Total_GWP"] / df["ftd"]
    df["GWP_E"]   = df["Total_GWP"] / df["E_modulus"]
    df["GWP_fcd_m3"] = df["Total_GWP_m3"] / df["fcd"]
    df["GWP_ftd_m3"] = df["Total_GWP_m3"] / df["ftd"]
    df["GWP_E_m3"] = df["Total_GWP_m3"] / df["E_modulus"]

print("check nach normierung")
print(dfCLT["fcd"])
print(dfCLT["GWP_fcd"])
# BSH zusammenfassen (GL-Klassen)
dfBSH = pd.concat([dfGL24, dfGL28, dfGL30, dfGL32])

# ----------------------------------------
# Y-Positionen
# ----------------------------------------
y_positions = {
    "C20/25 (#2)": 15,
    "C25/30 (#8)": 14,
    "C30/37 (#23)": 13,
    "BSP (#24)": 11,
    "KVH (#5)": 10,
    "BSH (#8)": 9,
    "B500B (#11)": 7,
    "andere BSt (#6)": 6,
    "Baustahl (#22)": 4,
    "Spannstahl (#2)": 2,
}



# ----------------------------------------
# Plot-Funktion
# ----------------------------------------
def plot_data(ax, x_col, factor = 1.0):
    # Beton

    ax.scatter(dfC2025[x_col] * factor, np.full(len(dfC2025), y_positions["C20/25 (#2)"]), color="lightgreen")
    ax.scatter(dfC2530[x_col] * factor, np.full(len(dfC2530), y_positions["C25/30 (#8)"]), color="green")
    ax.scatter(dfC3037[x_col] * factor, np.full(len(dfC3037), y_positions["C30/37 (#23)"]), color="darkgreen")
    # plt.scatter(dfC3037[x_col] * factor, jitter(y_positions["Hochbaubeton"], len(dfC3037)), color="darkgreen")6

    # Holz
    ax.scatter(dfCLT[x_col] * factor, np.full(len(dfCLT), y_positions["BSP (#24)"]), color="red")
    ax.scatter(dfKVH[x_col] * factor, np.full(len(dfKVH), y_positions["KVH (#5)"]), color="darkorange")
    ax.scatter(dfBSH[x_col] * factor, np.full(len(dfBSH), y_positions["BSH (#8)"]), color="orange")

    # Stahl
    ax.scatter(dfB500B[x_col] * factor, np.full(len(dfB500B), y_positions["B500B (#11)"]), color="lightblue")
    ax.scatter(dfRebar[x_col] * factor, np.full(len(dfRebar), y_positions["andere BSt (#6)"]), color="blue")

    # Baustahl
    ax.scatter(dfSteel[x_col] * factor, np.full(len(dfSteel), y_positions["Baustahl (#22)"]), color="darkblue")

    # Spannstahl
    ax.scatter(dfPosttension[x_col] * factor, np.full(len(dfPosttension), y_positions["Spannstahl (#2)"]), color="grey")

    # Linien
    ax.axhline(12, linestyle="--", color="grey")
    ax.axhline(8, linestyle="--", color="grey")
    ax.axhline(5, linestyle="--", color="grey")
    ax.axhline(3, linestyle="--", color="grey")

    ax.grid(axis="x", linestyle=":", alpha=0.5)

plt.rcParams["font.family"] = "Times New Roman"

#  Math-Schrift auf Times setzen
plt.rcParams["mathtext.fontset"] = "stix"
plt.rcParams["mathtext.rm"] = "Times New Roman"
plt.rcParams["mathtext.it"] = "Times New Roman:italic"

plt.rcParams.update({
    "font.size": 14
})
# ----------------------------------------
# Figure 2x2 auf t bezogen
# ----------------------------------------
fig, axes = plt.subplots(3, 2, figsize=(12, 12), sharey=False)

# ----------------------------------------
# Achsen formatieren
# ----------------------------------------
for ax in axes.flatten():
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))
    ax.set_ylim(0, 15.5)

# ----------------------------------------
# Subplot 1: GWP / fcd
# ----------------------------------------
factor = 1e6  # N/m² → MPa
plot_data(axes[0, 0], "GWP_fcd", factor)
axes[0, 0].set_xlabel(r"GWP / ${f_{cd}}$ [kg CO₂-eq $\cdot$ t$^{-1}$ / MPa]")
#axes[0, 0].set_title("Normierung mit fcd")

# ----------------------------------------
# Subplot 2: GWP / ftd
# ----------------------------------------
plot_data(axes[1, 0], "GWP_ftd", factor)
axes[1, 0].set_xlabel(r"GWP / ${f_{ct}}$ [kg CO₂-eq $\cdot$ t$^{-1}$ / MPa]")
#axes[0, 1].set_title("Normierung mit ftd")

# ----------------------------------------
# Subplot 3: GWP / E-Modul
# ----------------------------------------
plot_data(axes[2, 0], "GWP_E", 1e9)
axes[2, 0].set_xlabel(r"GWP / $E$ [kg CO₂-eq $\cdot$ t$^{-1}$ / GPa]")
#axes[1, 0].set_title("Normierung mit E-Modul")



# ----------------------------------------
# Subplot 1: GWP / fcd
# ----------------------------------------
plot_data(axes[0, 1], "GWP_fcd_m3", factor)
axes[0, 1].set_xlabel(r"GWP / ${f_{cd}}$ [kg CO₂-eq $\cdot$ m$^{-3}$ / MPa)]")
#axes[0, 0].set_title("Normierung mit fcd")

# ----------------------------------------
# Subplot 2: GWP / ftd
# ----------------------------------------
plot_data(axes[1, 1], "GWP_ftd_m3", factor)
axes[1, 1].set_xlabel(r"GWP / ${f_{td}}$ [kg CO₂-eq $\cdot$ m$^{-3}$ / MPa]")
#axes[0, 1].set_title("Normierung mit ftd")

# ----------------------------------------
# Subplot 3: GWP / E-Modul
# ----------------------------------------
plot_data(axes[2, 1], "GWP_E_m3",1e9)
axes[2, 1].set_xlabel(r"GWP / $E$ [kg CO₂-eq $\cdot$ m$^{-3}$ / GPa]")
#axes[1, 0].set_title("Normierung mit E-Modul")

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
"""
#scientific numbers
for ax in axes.flatten():
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((0, 0))
    ax.xaxis.set_major_formatter(formatter)
"""

# ----------------------------------------
# Layout
# ----------------------------------------
plt.tight_layout()

# Dateiname
filename = "GWP_plot_normiert"

# Speicherung als PDF (vektorbasiert → perfekt für Paper)
plt.savefig(f"{filename}.pdf",
            bbox_inches="tight",
            dpi=300)

# Speicherung als JPG (für Bericht / Präsentation)
plt.savefig(f"{filename}.jpg",
            bbox_inches="tight",
            dpi=300)

plt.show()
