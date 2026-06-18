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
#extract values for structural steel
#
inquiry = (""" 
        SELECT PRO_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Structural_steel_profile%'
        AND "MECH_PROP" LIKE '%S355%'
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
        AND "MECH_PROP" LIKE '%Y1860%'
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

# ------------------------------------------------------------------------------------------------------------------------
# Funktion zur Berechnung der Kennwerte
def print_stats(df, name):
    print(f"\nStatistik für {name}:")

    # Mittelwert
    mean_gwp = df["Total_GWP"].mean()
    mean_gwp_m3 = df["Total_GWP_m3"].mean()

    # Quantile
    q10_gwp = df["Total_GWP"].quantile(0.10)
    q90_gwp = df["Total_GWP"].quantile(0.90)

    q10_gwp_m3 = df["Total_GWP_m3"].quantile(0.10)
    q90_gwp_m3 = df["Total_GWP_m3"].quantile(0.90)

    print("Total_GWP:")
    print(f"  Mittelwert: {mean_gwp}")
    print(f"  10%-Quantil: {q10_gwp}")
    print(f"  90%-Quantil: {q90_gwp}")

    print("Total_GWP_m3:")
    print(f"  Mittelwert: {mean_gwp_m3}")
    print(f"  10%-Quantil: {q10_gwp_m3}")
    print(f"  90%-Quantil: {q90_gwp_m3}")


# ------------------------------------------------------------------------------------------------------------------------
# Aufruf für alle Produkte

print_stats(dfC2025, "C20/25")
print_stats(dfC2530, "C25/30")
print_stats(dfC3037, "C30/37")
print_stats(dfGL24, "GL24")
print_stats(dfKVHC24, "KVH C24")
print_stats(dfB500B, "B500B")
print_stats(dfSteel, "Baustahl")
print_stats(dfPosttension, "Spannstahl")