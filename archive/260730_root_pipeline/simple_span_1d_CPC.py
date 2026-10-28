# file contains code for generating of example "simple supported beam in wood and reinforced concrete and
# different cross-sections"

# IMPORT
# import create_dummy_database  # file for creating a "dummy database", for test propose
import struct_analysis  # file with code for structural analysis
import opt_and_plot  # file with code for plotting results in a standardized way
import matplotlib.pyplot as plt
import numpy as np
import class_to_excel


# define system lengths for plot (Datapoints on x-Axis of plot)
lengths = [ 4, 12]

# Index of verified length (cross-sections of that length will be plotted)
idx_vrc = 4

# max. number of iterations per optimization. Higher value leads to better results
max_iter = 100

#  define content of plot
criteria = ["ENV"]  # envelop, all criteria should be fulfilled (ULS, SLS1, SLS2, Fire)
optima = ["GWP"]  # optimizing cross-sections for minimal GWP

# define database
database_name = "database_260304.db"
# database_name = "dummy_sustainability.db"  # define database name
# create_dummy_database.create_database(database_name)  # create database

# create floor structure for solid wooden cross-section
bodenaufbau_vollholzdecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                                 ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                                 ["'Kies gebrochen'", 0.12, False]]
bodenaufbau_wd_solid = struct_analysis.FloorStruc(bodenaufbau_vollholzdecke, database_name)

# create floor structure for ribbed wooden cross-section
# For reaching REI60, Lignum 4.1, Table 433-2, Column G is applied. Thus, Gipsfaserplatte (2x15 mm) and Steinwolle
# (180 mm) are required as non load bearing layers.
h_ins = 0.18
bodenaufbau_hohlkastendecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                                 ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Gipsfaserplatte'", 0.03, False], ["'Glaswolle'", 0.03, False],
                                 ["'Kies gebrochen'", 0.12, False], ["'Steinwolle'", h_ins, False],]
bodenaufbau_wd_rib = struct_analysis.FloorStruc(bodenaufbau_hohlkastendecke, database_name)
# correct the total height of the floor structure by the height of the insulation within the element
bodenaufbau_wd_rib.h = bodenaufbau_wd_rib.h - h_ins

# create floor structure for solid reinforced concrete cross-section
bodenaufbau_rcdecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False]]
bodenaufbau_rc = struct_analysis.FloorStruc(bodenaufbau_rcdecke, database_name)

# create floor structure for ribbed reinforced concrete cross-section
bodenaufbau_rcdecke_slim = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False],["'Kies gebrochen'", 0.06, False]]
bodenaufbau_rc_rib = struct_analysis.FloorStruc(bodenaufbau_rcdecke_slim, database_name)

# define loads on member
g2k = 0.75e3  # n.t. Einbauten
qk = 2e3  # Nutzlast

# define service limit state criteria
req = struct_analysis.Requirements()


def max_of_arrays(existing_data, new_data):
    return [max(a, b) for a, b in zip(existing_data, new_data)]


data_max = [0, 0, 0, 0]
vrfctn_members = []

#-----------------------------------------------------------------------------------------------------------------------
# CREATE AND PLOT DATASET FOR RECTANGULAR AND RIBBED WOODEN CROSS-SECTIONS

# define materials for which date is searched in the database (table products, attribute material)
#mat_names = ["'Glue_laminated_timber'", "'Glue_laminated_timber_board'", "'Solid_structural_timber'"]
mat_names = ["'Glue_laminated_timber'"]#, "'3_and_5_plywood'", "'Solid_structural_timber'"]

#TODO: Glue Laminated Timberboard: 3-Schichtplatten / CLT Platten: Prüfen, sind die mech. Eigenschaften und das Trägheitsmoment richtig berücksichtigt? Also z.B: mit Faktor 2/3?

# retrieve data from database, find optimal cross-sections and plot results for solid cross-section
data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(lengths, database_name, criteria, optima,
                                                              bodenaufbau_wd_solid, req, "wd_rec", mat_names,
                                                              g2k, qk, max_iter, idx_vrc)
data_max = max_of_arrays(data_max, data_max_new)
vrfctn_members.append(vrfctn_members_new)
"""
mat_names = ["'Glue_laminated_timber'", "'Solid_structural_timber'"]
# retrieve data from database, find optimal cross-sections and plot results for ribbed cross-section
data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(lengths, database_name, criteria, optima,
                                                              bodenaufbau_wd_rib, req, "wd_rib", mat_names,
                                                              g2k, qk, max_iter, idx_vrc)
data_max = max_of_arrays(data_max, data_max_new)
vrfctn_members.append(vrfctn_members_new)
"""
#-----------------------------------------------------------------------------------------------------------------------
# CREATE AND PLOT DATASET FOR RECTANGULAR AND RIBBED REINFORCED CONCRETE CROSS-SECTIONS
# define materials for which date is searched in the database (table products, attribute material)
mat_names = ["'ready_mixed_concrete'"]


# retrieve data from database, find optimal cross-sections and plot results for solid cross-section
data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(lengths, database_name, criteria, optima, bodenaufbau_rc,
                                                              req, "rc_rec", mat_names, g2k, qk, max_iter,
                                                              idx_vrc)
data_max = max_of_arrays(data_max, data_max_new)
vrfctn_members.append(vrfctn_members_new)
"""

# retrieve data from database, find optimal cross-sections and plot results for ribbed cross-section
data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(lengths, database_name, criteria, optima,
                                                              bodenaufbau_rc_rib, req, "rc_rib", mat_names,
                                                              g2k, qk, max_iter, idx_vrc)
data_max = max_of_arrays(data_max, data_max_new)
vrfctn_members.append(vrfctn_members_new)
"""
# DEFINE LABELS OF PLOTS
plotted_data = [["h$_{struct}$", "[m]"], ["h$_{tot}$", "[m]"], ["GWP$_{struct}$", "[kg-CO$_2$-eq]"], ["GWP$_{tot}$", "[kg-CO$_2$-eq]"]]

# ADD LABELS, LEGEND, AXIS LIMITS AND GRID TO THE PLOTS
for idx, info in enumerate(plotted_data):
    plt.subplot(2, 2, idx + 1)
    plt.xlabel('l [m]', fontsize =12)
    plt.ylabel(info[0] + " " + info[1], fontsize=12)
    if idx % 2 == 0:
        plt.axis((min(lengths), max(lengths), 0, max(data_max[idx], data_max[idx+1])))
    else:
        plt.axis((min(lengths), max(lengths), 0, max(data_max[idx], data_max[idx-1])))
    plt.grid()
# __________________________________________________________________________________________________________
# Daten CPC Platten
class CPC:
    class Einfeld:
        span = np.array([4, 6, 7, 8, 10, 10, 12, 12]) # Spannweite
        h_struct = np.array([0.072, 0.192, 0.272, 0.372, 0.592, 0.392, 0.692, 0.592])  # Höhe der Tragstruktur
        h_tot = np.array([0.18, 0.30, 0.38, 0.48, 0.70, 0.50, 0.80, 0.70])  # Höhe des gesamten Bodenaufbaus
        GWP_struct = np.array([38, 44, 50, 56, 67, 79, 89, 100])  # GWP Tragstruktur
        GWP_tot = np.array([92, 98, 104, 110, 122, 133, 144, 155])  # GWP total

    class Zweifeld:
        span = np.array([4, 6, 8, 10, 12])
        h_struct = np.array([0.032, 0.092, 0.172, 0.292, 0.412])
        h_tot = np.array([0.14, 0.20, 0.28, 0.40, 0.52])
        GWP_struct = np.array([39, 44, 48, 55, 65])
        GWP_tot = np.array([94, 98, 102, 109, 119])

# __________________________________________________________________________________________________________
plt.subplot(2,2,1)
plt.scatter(CPC.Einfeld.span, CPC.Einfeld.h_struct,marker='o', label='Einfeld')
plt.scatter(CPC.Zweifeld.span, CPC.Zweifeld.h_struct,marker='D', label='Zweifeld')
plt.subplot(2,2,2)
plt.scatter(CPC.Einfeld.span, CPC.Einfeld.h_tot,marker='o', label='Einfeld')
plt.scatter(CPC.Zweifeld.span, CPC.Zweifeld.h_tot,marker='D', label='Zweifeld')
plt.subplot(2,2,3)
plt.scatter(CPC.Einfeld.span, CPC.Einfeld.GWP_struct,marker='o', label='Einfeld')
plt.scatter(CPC.Zweifeld.span, CPC.Zweifeld.GWP_struct,marker='D', label='Zweifeld')
plt.subplot(2,2,4)
plt.scatter(CPC.Einfeld.span, CPC.Einfeld.GWP_tot,marker='o', label='Einfeld')
plt.scatter(CPC.Zweifeld.span, CPC.Zweifeld.GWP_tot,marker='D', label='Zweifeld')

"""
 # # plot cross-section of members for verification
for mem_group in vrfctn_members:
     for i, mem in enumerate(mem_group[0]):
         section = mem.section
         opt_and_plot.plot_section(section)
         # Show the plot
         plt.title(f'#{mem_group[1][i]}')
"""
# SHOW FIGURE
plt.show()

class_to_excel.class_to_excel(CPC, "CPC_Daten.xlsx", folder="Resultate")

Test=1