import matplotlib.pyplot as plt
import sqlite3
import numpy as np
import pandas as pd
import statistics
import struct_analysis  # file with code for structural analysis
import os

# define database
database_name = "database_260506_Hochbau.db"
#connect to the database
connection = sqlite3.connect(database_name)
# create cursor object
cursor = connection.cursor()
#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C20/25
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C20/25%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC2025 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfC2025["PROD_ID"])
print(dfC2025["DENSITY"])
print(dfC2025["Total_GWP"])
print(dfC2025["Total_GWP_m3"])
print(dfC2025["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C25/30
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C25/30%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC2530 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfC2530["PROD_ID"])
print(dfC2530["DENSITY"])
print(dfC2530["Total_GWP"])
print(dfC2530["Total_GWP_m3"])
print(dfC2530["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for concrete C30/37
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND MECH_PROP LIKE '%C30/37%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfC3037 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfC3037["PROD_ID"])
print(dfC3037["DENSITY"])
print(dfC3037["Total_GWP"])
print(dfC3037["Total_GWP_m3"])
print(dfC3037["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for all concrete Hochbau
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND (MECH_PROP LIKE '%C20/25%' OR MECH_PROP LIKE '%C25/30%' OR MECH_PROP LIKE '%C30/37%')
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfHochbaubeton = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfHochbaubeton["PROD_ID"])
print(dfHochbaubeton["DENSITY"])
print(dfHochbaubeton["Total_GWP"])
print(dfHochbaubeton["Total_GWP_m3"])
print(dfHochbaubeton["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL24
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL24%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL24 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfGL24["PROD_ID"])
print(dfGL24["DENSITY"])
print(dfGL24["Total_GWP"])
print(dfGL24["Total_GWP_m3"])
print(dfGL24["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL28
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL28%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL28 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfGL28["PROD_ID"])
print(dfGL28["DENSITY"])
print(dfGL28["Total_GWP"])
print(dfGL28["Total_GWP_m3"])
print(dfGL28["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL30
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL30%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL30 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfGL30["PROD_ID"])
print(dfGL30["DENSITY"])
print(dfGL30["Total_GWP"])
print(dfGL30["Total_GWP_m3"])
print(dfGL30["MECH_PROP"])
#------------------------------------------------------------------------------------------------------------------------
#extract values for all GL (BSH)
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP IS NOT NULL
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfBSH = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfBSH["PROD_ID"])
print(dfBSH["DENSITY"])
print(dfBSH["Total_GWP"])
print(dfBSH["Total_GWP_m3"])
print(dfBSH["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber GL32
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%Glue_laminated_timber%'
        AND MECH_PROP LIKE '%GL32%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfGL32 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfGL32["PROD_ID"])
print(dfGL32["DENSITY"])
print(dfGL32["Total_GWP"])
print(dfGL32["Total_GWP_m3"])
print(dfGL32["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for Timber C24
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "PRODUCT_NAME" LIKE '%KVH%'
        AND MECH_PROP LIKE '%C24%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfKVHC24 = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfKVHC24["PROD_ID"])
print(dfKVHC24["DENSITY"])
print(dfKVHC24["Total_GWP"])
print(dfKVHC24["Total_GWP_m3"])
print(dfKVHC24["MECH_PROP"])

#------------------------------------------------------------------------------------------------------------------------
#extract values for CLT
#
inquiry = (""" 
        SELECT PROD_ID, DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP, PRODUCT_NAME FROM products
        WHERE DENSITY IS NOT NULL
        AND "PRODUCT_NAME" LIKE '%CLT%'
        AND MECH_PROP IS NOT NULL
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND ValidEPD = 1
        AND Man_Ausschluss = 1 """
           )
cursor.execute(inquiry)
result = cursor.fetchall()

dfCLT = pd.DataFrame(result, columns=["PROD_ID", "DENSITY", "Total_GWP", "Total_GWP_m3", "MECH_PROP", "PRODUCT_NAME"])

print(dfCLT["PROD_ID"])
print(dfCLT["DENSITY"])
print(dfCLT["Total_GWP"])
print(dfCLT["Total_GWP_m3"])
print(dfCLT["MECH_PROP"])