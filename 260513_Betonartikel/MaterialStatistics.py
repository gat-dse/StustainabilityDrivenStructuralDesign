import matplotlib.pyplot as plt
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
#           SINGLE     PLOT       TOTAL GWP
#________________________________________________________________________________________________________________________


# -----------------------
# Kategorien (Y-Positionen)
# -----------------------
y_positions = {
    "C20/25": 17,
    "C25/30": 16,
    "C30/37": 15,
    "CLT": 13,
    "KVH": 11,
    "BSH": 9,
    "B500B": 7,
    "Bewehrungsstahl allg.": 6,
    "Baustahl": 4,
    "Spannstahl": 2,
}
"""
# -----------------------
# Plot
# -----------------------
plt.figure(figsize=(6.3, 4))

# Beton (grün)

def jitter(y, n):
    return y + np.random.uniform(-0.1, 0.1, n)


plt.scatter(dfC2025["Total_GWP"], np.full(len(dfC2025), y_positions["C20/25"]), color="lightgreen")
plt.scatter(dfC2530["Total_GWP"], np.full(len(dfC2530), y_positions["C25/30"]), color="green")
plt.scatter(dfC3037["Total_GWP"], np.full(len(dfC3037), y_positions["C30/37"]), color="darkgreen")
#plt.scatter(dfC3037["Total_GWP"], jitter(y_positions["C30/37"], len(dfC3037)), color="dark green")
# Holz (orange)
plt.scatter(dfCLT["Total_GWP"], np.full(len(dfCLT), y_positions["CLT"]), color="orange")
plt.scatter(dfKVHC24["Total_GWP"], np.full(len(dfKVHC24), y_positions["KVH"]), color="orange")
plt.scatter(dfBSH["Total_GWP"], np.full(len(dfBSH), y_positions["BSH"]), color="orange")

# Bewehrungsstahl (blau)
plt.scatter(dfRebar["Total_GWP"], np.full(len(dfRebar), y_positions["B500B"]), color="lightblue")

# Baustahl:
plt.scatter(dfSteel["Total_GWP"], np.full(len(dfSteel), y_positions["Steel"]), color="darkblue")


# -----------------------
# Achsen & Labels
# -----------------------
plt.yticks(list(y_positions.values()), list(y_positions.keys()))
plt.xlabel("Total GWP [kg CO₂-eq / t]")
plt.ylabel("Material")

# Trennlinien (wie in Skizze)
plt.axhline(9, linestyle="--", color="grey")   # zwischen Beton und Holz
plt.axhline(5, linestyle="--", color="grey")   # zwischen Holz und Bewehrungsstahl
plt.axhline(3, linestyle="--", color="grey")   # zwischen Bewehrungsstahl und Stahl

plt.grid(axis="x", linestyle=":", alpha=0.5)

plt.tight_layout()
plt.show()

#________________________________________________________________________________________________________________________
#           BOTH     PLOTS       TOTAL GWP and TOTAL GWP M3
#________________________________________________________________________________________________________________________

import matplotlib.pyplot as plt
import numpy as np

# -----------------------
# Kategorien (Y-Positionen)
# -----------------------
y_positions = {
    
    "C20/25": 17,
    "C25/30": 16,
    "C30/37": 15,
    "CLT": 13,
    "KVH": 11,
    "BSH": 9,
    "B500B": 7,
    "Bewehrungsstahl allg.": 6,
    "Baustahl": 4,
    "Spannstahl": 2,
}

# -----------------------
# Figure mit 2 Subplots
# -----------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

# ==========================================================
# LINKS: Total_GWP
# ==========================================================
ax = axes[0]

# Beton
ax.scatter(dfC2025["Total_GWP"], np.full(len(dfC2025), y_positions["C20/25"]), color="lightgreen")
ax.scatter(dfC2530["Total_GWP"], np.full(len(dfC2530), y_positions["C25/30"]), color="green")
ax.scatter(dfC3037["Total_GWP"], np.full(len(dfC3037), y_positions["C30/37"]), color="darkgreen")

# Holz
ax.scatter(dfCLT["Total_GWP"], np.full(len(dfCLT), y_positions["CLT"]), color="orange")
ax.scatter(dfKVHC24["Total_GWP"], np.full(len(dfKVHC24), y_positions["KVH"]), color="orange")
ax.scatter(dfBSH["Total_GWP"], np.full(len(dfBSH), y_positions["BSH"]), color="orange")

# Stahl
ax.scatter(dfRebar["Total_GWP"], np.full(len(dfRebar), y_positions["B500B"]), color="lightblue")
ax.scatter(dfSteel["Total_GWP"], np.full(len(dfSteel), y_positions["Steel"]), color="darkblue")

# Formatierung
ax.set_title("Total GWP [kg CO₂-eq / t]")
ax.set_xlabel("GWP")
ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(list(y_positions.keys()))

ax.axhline(9, linestyle="--", color="grey")
ax.axhline(5, linestyle="--", color="grey")
ax.axhline(3, linestyle="--", color="grey")

ax.grid(axis="x", linestyle=":", alpha=0.5)

# ==========================================================
# RECHTS: Total_GWP_m3
# ==========================================================
ax = axes[1]

# Beton
ax.scatter(dfC2025["Total_GWP_m3"], np.full(len(dfC2025), y_positions["C20/25"]), color="lightgreen")
ax.scatter(dfC2530["Total_GWP_m3"], np.full(len(dfC2530), y_positions["C25/30"]), color="green")
ax.scatter(dfC3037["Total_GWP_m3"], np.full(len(dfC3037), y_positions["C30/37"]), color="darkgreen")

# Holz
ax.scatter(dfCLT["Total_GWP_m3"], np.full(len(dfCLT), y_positions["CLT"]), color="orange")
ax.scatter(dfKVHC24["Total_GWP_m3"], np.full(len(dfKVHC24), y_positions["KVH"]), color="orange")
ax.scatter(dfBSH["Total_GWP_m3"], np.full(len(dfBSH), y_positions["BSH"]), color="orange")

# Stahl
ax.scatter(dfRebar["Total_GWP_m3"], np.full(len(dfRebar), y_positions["B500B"]), color="lightblue")
ax.scatter(dfSteel["Total_GWP_m3"], np.full(len(dfSteel), y_positions["Steel"]), color="darkblue")

# Formatierung
ax.set_title("Total GWP [kg CO₂-eq / m³]")
ax.set_xlabel("GWP")

ax.axhline(9, linestyle="--", color="grey")
ax.axhline(5, linestyle="--", color="grey")
ax.axhline(3, linestyle="--", color="grey")

ax.grid(axis="x", linestyle=":", alpha=0.5)

# -----------------------
# Layout
# -----------------------
plt.tight_layout()
plt.show()
"""
#________________________________________________________________________________________________________________________
#           BOTH     PLOTS       TOTAL GWP and TOTAL GWP M3 as 2 x 2 Plot
#________________________________________________________________________________________________________________________



y_positions = {
    "C20/25": 15,
    "C25/30": 14,
    "C30/37": 13,
    "BSP": 11,
    "KVH": 10,
    "BSH": 9,
    "B500B": 7,
    "Bewehrungsstahl allg.": 6,
    "Baustahl": 4,
    "Spannstahl": 2,
}
def jitter(y, n):
    return y + np.random.uniform(-0.1, 0.1, n)

def plot_data(ax, x_col):
    # Beton

    ax.scatter(dfC2025[x_col], np.full(len(dfC2025), y_positions["C20/25"]), color="lightgreen")
    ax.scatter(dfC2530[x_col], np.full(len(dfC2530), y_positions["C25/30"]), color="green")
    ax.scatter(dfC3037[x_col], np.full(len(dfC3037), y_positions["C30/37"]), color="darkgreen")
    #plt.scatter(dfC3037[x_col], jitter(y_positions["Hochbaubeton"], len(dfC3037)), color="darkgreen")6

    # Holz
    ax.scatter(dfCLT[x_col], np.full(len(dfCLT), y_positions["BSP"]), color="red")
    ax.scatter(dfKVHC24[x_col], np.full(len(dfKVHC24), y_positions["KVH"]), color="darkorange")
    ax.scatter(dfBSH[x_col], np.full(len(dfBSH), y_positions["BSH"]), color="orange")

    # Bewehrungsstahl
    ax.scatter(dfRebar[x_col], np.full(len(dfRebar), y_positions["B500B"]), color="lightblue")
    ax.scatter(dfRebar[x_col], np.full(len(dfRebar), y_positions["Bewehrungsstahl allg."]), color="blue")

    #Baustahl
    ax.scatter(dfSteel[x_col], np.full(len(dfSteel), y_positions["Baustahl"]), color="darkblue")

    #Spannstahl
    ax.scatter(dfPosttension[x_col], np.full(len(dfSteel), y_positions["Spannstahl"]), color="darkblue")


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
fig, axes = plt.subplots(3, 2, figsize=(12, 8), sharey=False,gridspec_kw={"height_ratios": [2, 1, 1]})



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
axes[0, 0].set_xlim(0, 1400)
axes[0, 0].set_ylim(0, 13.5)

# -----------------------
# OBEN RECHTS
# -----------------------
plot_data(axes[0, 1], "Total_GWP_m3")
#axes[0, 1].set_title("Total GWP [kg CO₂-eq / m³]")
axes[0, 1].set_xlabel("Total GWP [kg CO₂-eq / m³]")
axes[0, 1].set_xlim(0, 10000)
axes[0, 1].set_ylim(0, 13.5)

# -----------------------
# Mitte LINKS zoom Beton
# -----------------------
plot_data(axes[1, 0], "Total_GWP")
axes[1, 0].set_xlim(0, 130)
axes[1, 0].set_ylim(9, 13.5)
axes[1, 0].set_xlabel("Total GWP [kg CO₂-eq / t]")

# -----------------------
# Mitte RECHTS zoom Beton
# -----------------------
plot_data(axes[1, 1], "Total_GWP_m3")
axes[1, 1].set_xlim(0, 350)
axes[1, 1].set_ylim(9, 13.5)
axes[1, 1].set_xlabel("Total GWP [kg CO₂-eq / m³]")

# -----------------------
# Unten LINKS zoom Holz
# -----------------------
plot_data(axes[2, 0], "Total_GWP")
axes[2, 0].set_xlim(0, 500)
axes[2, 0].set_ylim(5, 9)
axes[2, 0].set_xlabel("Total GWP [kg CO₂-eq / t]")

# -----------------------
# unten RECHTS zoom Holz
# -----------------------
plot_data(axes[2, 1], "Total_GWP_m3")
axes[2, 1].set_xlim(0, 350)
axes[2, 1].set_ylim(5, 9)
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

# -----------------------
# Layout
# -----------------------
plt.tight_layout()
plt.show()
