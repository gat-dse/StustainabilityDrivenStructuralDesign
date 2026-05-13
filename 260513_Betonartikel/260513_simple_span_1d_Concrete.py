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
lengths = [7,7]

# Index of verified length (cross-sections of that length will be plotted)
idx_vrc = 4

# max. number of iterations per optimization. Higher value leads to better results
max_iter = 10

#  define content of plot
criteria = ["ENV"]  # envelop, all criteria should be fulfilled (ENV, ULS, SLS1, SLS2, Fire)
optima = ["GWP"]  # optimizing cross-sections for minimal GWP

# define database
database_name = "database_260506.db"
# database_name = "dummy_sustainability.db"  # define database name
# create_dummy_database.create_database(database_name)  # create database


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


# Start der Optimierung
start = time.time()



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


# retrieve data from database, find optimal cross-sections and plot results for ribbed cross-section
data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(lengths, database_name, criteria, optima,
                                                              bodenaufbau_rc_rib, req, "rc_rib", mat_names,
                                                              g2k, qk, max_iter, idx_vrc)
data_max = max_of_arrays(data_max, data_max_new)
vrfctn_members.append(vrfctn_members_new)

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

# # # plot cross-section of members for verification
# for mem_group in vrfctn_members:
#     for i, mem in enumerate(mem_group[0]):
#         section = mem.section
#         plot_datasets.plot_section(section)
#         # Show the plot
#         plt.title(f'#{mem_group[1][i]}')

# SHOW FIGURE
plt.show()

#Ende der Optimierung
ende = time.time()
dauer = ende - start

print(f"Die Optimierung dauerte {round(dauer, 2)} Sekunden.")

#Save Data in database:
