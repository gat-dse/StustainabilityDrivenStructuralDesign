# TEST IF EPDs ARE PROPERLY CHOSEN
# define database
database_name = "database_260304.db"
#import functions
import struct_analysis  # file with code for structural analysis
import struct_optimization  # file with code for structural optimization
import sqlite3  # import modul for SQLite
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon
from scipy.interpolate import interp1d

connection = sqlite3.connect(database_name)
cursor = connection.cursor()

to_plot = []
# _____________________________________________________________________________________________________________________
# check Glued laminated timber
mat_names = ["'Glue_laminated_timber'"]
# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
for mat_name in mat_names:
    inquiry = ("""
            SELECT PRO_ID, MECH_PROP, "Total_GWP" FROM products
            WHERE DENSITY IS NOT NULL
            AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
            AND MECH_PROP IS NOT NULL
            AND ValidEPD = 1 
            AND "MATERIAL" LIKE """ + mat_name
               )
    # inquiry = ("SELECT PRO_ID FROM products WHERE"
    #            " material=" + mat_name)
    cursor.execute(inquiry)
    result = cursor.fetchall()
    GLULAMprod_id, GLULAMmech_prop, GLULAM_GWP = zip(*result)

# _____________________________________________________________________________________________________________________
# CHECK PLYWOOD
mat_names = ["'3- and 5-ply wood'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
for mat_name in mat_names:
    inquiry = ("""
            SELECT PRO_ID FROM products
            WHERE DENSITY IS NOT NULL
            AND MECH_PROP IS NOT NULL
            AND Statistik = 1 
            AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
            AND "SOURCE" NOT LIKE '%Ecoinvent%'
            AND "SOURCE" NOT LIKE '%KBOB%'
            AND "MATERIAL" LIKE """ + mat_name
               )
    # inquiry = ("SELECT PRO_ID FROM products WHERE"
    #            " material=" + mat_name)
    cursor.execute(inquiry)
    resultPLY = cursor.fetchall()
    for i, prod_id in enumerate(resultPLY):
        prod_id_str = "'" + str(prod_id[0]) + "'"
        inquiry = ("""
                SELECT MECH_PROP FROM products
                WHERE  PRO_ID LIKE """ + prod_id_str
                   )
        # inquiry = ("SELECT mech_prop FROM products WHERE"
        #            " PRO_ID=" + prod_id_str)
        cursor.execute(inquiry)
        resultPLY = cursor.fetchall()
        mech_propPLY = "'" + resultPLY[0][0] + "'"

# _____________________________________________________________________________________________________________________
# CHECK Solid structural timber

mat_names = ["'Solid_structural_timber'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
for mat_name in mat_names:
    inquiry = ("""
            SELECT PRO_ID FROM products
            WHERE DENSITY IS NOT NULL
            AND MECH_PROP IS NOT NULL
            AND Statistik = 1 
            AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
            AND "SOURCE" NOT LIKE '%Ecoinvent%'
            AND "SOURCE" NOT LIKE '%KBOB%'
            AND "MATERIAL" LIKE """ + mat_name
               )
    # inquiry = ("SELECT PRO_ID FROM products WHERE"
    #            " material=" + mat_name)
    cursor.execute(inquiry)
    resultTimber = cursor.fetchall()
    for i, prod_id in enumerate(resultTimber):
        prod_id_str = "'" + str(prod_id[0]) + "'"
        inquiry = ("""
                SELECT MECH_PROP FROM products
                WHERE  PRO_ID LIKE """ + prod_id_str
                   )
        # inquiry = ("SELECT mech_prop FROM products WHERE"
        #            " PRO_ID=" + prod_id_str)
        cursor.execute(inquiry)
        resultTimber = cursor.fetchall()
        mech_propTimber = "'" + resultTimber[0][0] + "'"

# _____________________________________________________________________________________________________________________
# CHECK ready mixed concrete


mat_names = ["'ready_mixed_concrete'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
for mat_name in mat_names:
    inquiry = ("""
            SELECT PRO_ID FROM products
            WHERE DENSITY IS NOT NULL
            AND MECH_PROP IS NOT NULL
            AND Statistik = 1 
            AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
            AND "SOURCE" NOT LIKE '%Ecoinvent%'
            AND "SOURCE" NOT LIKE '%KBOB%'
            AND "MATERIAL" LIKE """ + mat_name
               )
    # inquiry = ("SELECT PRO_ID FROM products WHERE"
    #            " material=" + mat_name)
    cursor.execute(inquiry)
    resultRC = cursor.fetchall()
    for i, prod_id in enumerate(resultRC):
        prod_id_str = "'" + str(prod_id[0]) + "'"
        inquiry = ("""
                SELECT MECH_PROP FROM products
                WHERE  PRO_ID LIKE """ + prod_id_str
                   )
        # inquiry = ("SELECT mech_prop FROM products WHERE"
        #            " PRO_ID=" + prod_id_str)
        cursor.execute(inquiry)
        resultRC = cursor.fetchall()
        mech_propRC = "'" + resultRC[0][0] + "'"

Test=1