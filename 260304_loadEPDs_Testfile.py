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
mat_names = ["'3_and_5_plywood'"]
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
    PLYprod_id, PLYmech_prop, PLY_GWP = zip(*result)


# _____________________________________________________________________________________________________________________
# CHECK Solid structural timber

mat_names = ["'Solid_structural_timber'"]

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
    STprod_id, STmech_prop, ST_GWP = zip(*result)

# _____________________________________________________________________________________________________________________
# CHECK ready mixed concrete


mat_names = ["'ready_mixed_concrete'"]

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
    RCprod_id, RCmech_prop, RC_GWP = zip(*result)

Test=1