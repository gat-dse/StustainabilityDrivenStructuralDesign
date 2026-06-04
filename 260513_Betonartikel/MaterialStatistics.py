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
#extract values for concrete
#
inquiry = (""" 
        SELECT DENSITY, Total_GWP, Total_GWP_m3, MECH_PROP FROM products
        WHERE DENSITY IS NOT NULL
        AND "MATERIAL" LIKE '%ready_mixed_concrete%'
        AND ("Copy for strength" IS NULL OR "Copy for strength" LIKE '%a%')
        AND MECH_PROP IS NOT NULL
        AND MECH_PROP NOT LIKE '%GL30%'
        AND ValidEPD = 1
        AND  MIN_MAX = 1
        AND Man_Ausschluss = 1 """