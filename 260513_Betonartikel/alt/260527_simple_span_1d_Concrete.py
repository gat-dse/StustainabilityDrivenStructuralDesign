# file contains code for generating of example "simple supported beam in wood and reinforced concrete and
# different cross-sections"

# IMPORT
# import create_dummy_database  # file for creating a "dummy database", for test propose
import struct_analysis  # file with code for structural analysis
#import plot_datasets  # file with code for plotting results in a standardized way
import opt_and_plot  # file with code for plotting results in a standardized way
import matplotlib.pyplot as plt
import time



# define system lengths for plot (Datapoints on x-Axis of plot)
lengths = [4,5]

# Index of verified length (cross-sections of that length will be plotted)
idx_vrc = 4

# max. number of iterations per optimization. Higher value leads to better results
max_iter = 10

#  define content of plot
criteria = ["ENV"]  # envelop, all criteria should be fulfilled (ENV, ULS, SLS1, SLS2, Fire)
optima = ["GWP"]  # optimizing cross-sections for minimal GWP

# define database
database_name = "database_260506_Hochbau.db"
# database_name = "dummy_sustainability.db"  # define database name
# create_dummy_database.create_database(database_name)  # create database


# create floor structure for solid reinforced concrete cross-section
bodenaufbau_rcdecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False]]
bodenaufbau_rc = struct_analysis.FloorStruc(bodenaufbau_rcdecke, database_name, name="massiv")

# create floor structure for ribbed reinforced concrete cross-section
bodenaufbau_rcdecke_slim = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False],["'Kies gebrochen'", 0.06, False]]
bodenaufbau_rc_rib = struct_analysis.FloorStruc(bodenaufbau_rcdecke_slim, database_name, name="Schuettung")

# define loads on member
g2k = 0.75e3  # n.t. Einbauten
qk = 2e3  # Nutzlast

# define service limit state criteria
req = struct_analysis.Requirements()


def max_of_arrays(existing_data, new_data):
    return [max(a, b) for a, b in zip(existing_data, new_data)]


data_max = [0, 0, 0, 0]
vrfctn_members = []


# Start der Optimierung
start = time.time()



#Ende der Optimierung
ende = time.time()
dauer = ende - start

print(f"Die Optimierung dauerte {round(dauer, 2)} Sekunden.")

#Save Data in database:
