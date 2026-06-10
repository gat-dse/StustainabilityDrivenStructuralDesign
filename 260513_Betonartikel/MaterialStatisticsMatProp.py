import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Times New Roman"
import sqlite3
import numpy as np
import pandas as pd
import statistics
import struct_analysis  # file with code for structural analysis
import os

# define database
database_name = "database_260610_Hochbau_neu.db"
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
        AND "PRODUCT_NAME" LIKE '%KVH%'
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
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfRebar = pd.DataFrame(result, columns=["PRO_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME", "ID", "Copy for strength"])
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


#_______________________________________________________________________________________________________________________
#_______________________________________________________________________________________________________________________
#_______________________________________________________________________________________________________________________


# alle DataFrames sammeln
dfs = [
    dfC2025, dfC2530, dfC3037,
    dfGL24, dfGL28, dfGL30, dfGL32,
    dfKVH, dfCLT,
    dfRebar, dfSteel
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
dfSteel = add_material_properties(dfSteel, df_mat)




# ----------------------------------------
# Normierte Werte berechnen
# ----------------------------------------
dfs_all = [
    dfC2025, dfC2530, dfC3037,
    dfGL24, dfGL28, dfGL30, dfGL32,
    dfKVH, dfCLT,
    dfRebar, dfSteel
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
    "C20/25": 10,
    "C25/30": 11,
    "C30/37": 12,
    "BSP": 8,
    "KVH": 7,
    "BSH": 6,
    "Bewehrungsstahl": 4,
    "Baustahl": 2
}

# ----------------------------------------
# Plot-Funktion
# ----------------------------------------
def plot_data(ax, x_col):

    # Beton
    ax.scatter(dfC2025[x_col], np.full(len(dfC2025), y_positions["C20/25"]), color="lightgreen")
    ax.scatter(dfC2530[x_col], np.full(len(dfC2530), y_positions["C25/30"]), color="green")
    ax.scatter(dfC3037[x_col], np.full(len(dfC3037), y_positions["C30/37"]), color="darkgreen")

    # Holz
    ax.scatter(dfCLT[x_col], np.full(len(dfCLT), y_positions["BSP"]), color="red")
    ax.scatter(dfKVH[x_col], np.full(len(dfKVH), y_positions["KVH"]), color="darkorange")
    ax.scatter(dfBSH[x_col], np.full(len(dfBSH), y_positions["BSH"]), color="orange")

    # Stahl
    ax.scatter(dfRebar[x_col], np.full(len(dfRebar), y_positions["Bewehrungsstahl"]), color="lightblue")
    ax.scatter(dfSteel[x_col], np.full(len(dfSteel), y_positions["Baustahl"]), color="darkblue")

    # Linien
    ax.axhline(9, linestyle="--", color="grey")
    ax.axhline(5, linestyle="--", color="grey")
    ax.axhline(3, linestyle="--", color="grey")

    ax.grid(axis="x", linestyle=":", alpha=0.5)


# ----------------------------------------
# Figure 2x2 auf t bezogen
# ----------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=False)

# ----------------------------------------
# Achsen formatieren
# ----------------------------------------
for ax in axes.flatten():
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))
    ax.set_ylim(0, 13.5)

# ----------------------------------------
# Subplot 1: GWP / fcd
# ----------------------------------------
plot_data(axes[0, 0], "GWP_fcd")
axes[0, 0].set_xlabel(r"GWP / ${f_{cd}}$ [kg CO₂-eq / t $\cdot$ N$\cdot$ m$^2$]")
#axes[0, 0].set_title("Normierung mit fcd")

# ----------------------------------------
# Subplot 2: GWP / ftd
# ----------------------------------------
plot_data(axes[0, 1], "GWP_ftd")
axes[0, 1].set_xlabel(r"GWP / ${f_{td}}$ [kg CO₂-eq / t $\cdot$ N$\cdot$ m$^2$]")
#axes[0, 1].set_title("Normierung mit ftd")

# ----------------------------------------
# Subplot 3: GWP / E-Modul
# ----------------------------------------
plot_data(axes[1, 0], "GWP_E")
axes[1, 0].set_xlabel(r"GWP / $E$ [kg CO₂-eq / t $\cdot$ N$\cdot$ m$^2$]")
#axes[1, 0].set_title("Normierung mit E-Modul")

# ----------------------------------------
# Subplot 4: GWP pro m³
# ----------------------------------------
plot_data(axes[1, 1], "Total_GWP")
axes[1, 1].set_xlabel(r"GWP [kg CO₂-eq / t]")
#axes[1, 1].set_title("GWP pro Volumen")
axes[1, 1].set_xlim(0, 1400)

# ----------------------------------------
# Layout
# ----------------------------------------
plt.tight_layout()
plt.show()


# ----------------------------------------
# Figure 2x2 auf m3 bezogen
# ----------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=False)

# ----------------------------------------
# Achsen formatieren
# ----------------------------------------
for ax in axes.flatten():
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))
    ax.set_ylim(0, 13.5)

# ----------------------------------------
# Subplot 1: GWP / fcd
# ----------------------------------------
plot_data(axes[0, 0], "GWP_fcd_m3")
axes[0, 0].set_xlabel(r"GWP / ${f_{cd}}$ [kg CO₂-eq / m³ $\cdot$ N$\cdot$ m$^2$]")
#axes[0, 0].set_title("Normierung mit fcd")

# ----------------------------------------
# Subplot 2: GWP / ftd
# ----------------------------------------
plot_data(axes[0, 1], "GWP_ftd_m3")
axes[0, 1].set_xlabel(r"GWP / ${f_{td}}$ [kg CO₂-eq / m³ $\cdot$ N$\cdot$ m$^2$]")
#axes[0, 1].set_title("Normierung mit ftd")

# ----------------------------------------
# Subplot 3: GWP / E-Modul
# ----------------------------------------
plot_data(axes[1, 0], "GWP_E_m3")
axes[1, 0].set_xlabel(r"GWP / $E$ [kg CO₂-eq / m³ $\cdot$ N$\cdot$ m$^2$]")
#axes[1, 0].set_title("Normierung mit E-Modul")

# ----------------------------------------
# Subplot 4: GWP pro m³
# ----------------------------------------
plot_data(axes[1, 1], "Total_GWP_m3")
axes[1, 1].set_xlabel(r"GWP [kg CO₂-eq / m³]")
axes[1, 1].set_xlim(0, 10000)
#axes[1, 1].set_title("GWP pro Volumen")

# ----------------------------------------
# Layout
# ----------------------------------------
plt.tight_layout()
plt.show()
