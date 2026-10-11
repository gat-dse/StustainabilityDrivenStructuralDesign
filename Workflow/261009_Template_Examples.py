# TEMPLATE for running examples: 1D members (simple beam / continuous / two span) in reinforced concrete and wood
# with different cross-sections. Copy this file, adjust the SETTINGS and activate the wanted entries in RUNS.

# IMPORT
import struct_analysis  # file with code for structural analysis
import opt_and_plot  # file with code for optimization and plotting results in a standardized way
import matplotlib.pyplot as plt
import time


#-----------------------------------------------------------------------------------------------------------------------
# SETTINGS
# define system lengths for plot (Datapoints on x-Axis of plot)
lengths = [4, 6, 8, 10]

# Index of verified length (cross-sections of that length will be plotted); must be < len(lengths), -1 = random
idx_vrc = len(lengths) - 1

# max. number of iterations per optimization. Higher value leads to better results
max_iter = 50

# optimization algorithm for rc sections: "basinhoppin" or "TPE" (wd_rec / wd_rib use their own algorithm)
alg = "TPE"

#  define content of plot
criteria = ["ENV"]  # options: "ULS", "SLS1" (deflections), "SLS2" (vibrations), "FIRE" (uppercase!), "ENV" (all
                    # together); available for all crsec_types; wd_rib: fire is not checked (penalty4 = 0), so "FIRE"
                    # gives no restriction and "ENV" does not include fire
optima = ["GWP"]  # options: "GWP" (min. GWP of cross-section), "h" (min. height of cross-section); several possible,
                  # e.g. ["GWP", "h"]; wd_rec ignores this (always smallest feasible h from fixed list); other values
                  # (e.g. "UBP") are not implemented and fail

# define database
database_name = "database_261009.db"
### KBOB: basetype input
basetype = "epd"  # data basis: "epd" (product EPDs) or "kbob" (generic KBOB v9.0 values)

# define loads on member
g2k = 0.75e3  # n.t. Einbauten
qk = 2e3  # Nutzlast

# define service limit state criteria
req = struct_analysis.Requirements()


#-----------------------------------------------------------------------------------------------------------------------
# FLOOR STRUCTURES (non load bearing layers: [product name, thickness or False for default, False])
# solid reinforced concrete cross-section
bodenaufbau_rcdecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False]]
bodenaufbau_rc = struct_analysis.FloorStruc(bodenaufbau_rcdecke, database_name, name="massiv")

# ribbed reinforced concrete cross-section (additional gravel)
bodenaufbau_rcdecke_slim = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                            ["'Unterlagsboden Zement, 85 mm'", False, False],
                            ["'Glaswolle'", 0.03, False], ["'Kies gebrochen'", 0.06, False]]
bodenaufbau_rc_rib = struct_analysis.FloorStruc(bodenaufbau_rcdecke_slim, database_name, name="Schuettung")

# solid wooden cross-section
bodenaufbau_vollholzdecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                             ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                             ["'Kies gebrochen'", 0.12, False]]
bodenaufbau_wd_solid = struct_analysis.FloorStruc(bodenaufbau_vollholzdecke, database_name, name="Vollholz")

# ribbed wooden cross-section (Hohlkastendecke)
# For reaching REI60, Lignum 4.1, Table 433-2, Column G is applied. Thus Steinwolle
# (180 mm) and Estrich (mind. 30mm) required as non load bearing layers.
h_ins = 0.18
bodenaufbau_hohlkastendecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                               ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                               ["'Kies gebrochen'", 0.12, False], ["'Steinwolle'", h_ins, False]]
bodenaufbau_wd_rib = struct_analysis.FloorStruc(bodenaufbau_hohlkastendecke, database_name, name="Hohlkasten")
# correct the total height of the floor structure by the height of the insulation within the element
bodenaufbau_wd_rib.h_Floor = bodenaufbau_wd_rib.h_Floor - h_ins


#-----------------------------------------------------------------------------------------------------------------------
# MATERIALS (table products, attribute material)
mat_names_rc = ["'ready_mixed_concrete'"]
mat_names_wd = ["'Glue_laminated_timber'", "'Solid_structural_timber'"]


#-----------------------------------------------------------------------------------------------------------------------
# RUNS: one entry = one dataset in the plot. Comment out entries that are not needed.
# crsec_type: "rc_rec", "rc_rib", "wd_rec", "wd_rib"
# system: "Simple Beam", "Continuous 1D", "Two span 1D 1D"
runs = [
    {"crsec_type": "rc_rec", "mat_names": mat_names_rc, "floorstruc": bodenaufbau_rc, "system": "Simple Beam"},
    # {"crsec_type": "rc_rec", "mat_names": mat_names_rc, "floorstruc": bodenaufbau_rc, "system": "Continuous 1D"},
    # {"crsec_type": "rc_rib", "mat_names": mat_names_rc, "floorstruc": bodenaufbau_rc_rib, "system": "Simple Beam"},
    # {"crsec_type": "rc_rib", "mat_names": mat_names_rc, "floorstruc": bodenaufbau_rc_rib, "system": "Continuous 1D"},
    # {"crsec_type": "wd_rec", "mat_names": mat_names_wd, "floorstruc": bodenaufbau_wd_solid, "system": "Simple Beam"},
    # {"crsec_type": "wd_rib", "mat_names": mat_names_wd, "floorstruc": bodenaufbau_wd_rib, "system": "Simple Beam"},
]


#-----------------------------------------------------------------------------------------------------------------------
# OPTIMIZATION
def max_of_arrays(existing_data, new_data):
    return [max(a, b) for a, b in zip(existing_data, new_data)]


data_max = [0, 0, 0, 0]
vrfctn_members = []

# Start der Optimierung
start = time.time()

for run in runs:
    # retrieve data from database, find optimal cross-sections and plot results
    data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(lengths, database_name, criteria, optima,
                                                                  run["floorstruc"], req, run["crsec_type"],
                                                                  run["mat_names"], g2k, qk, max_iter, idx_vrc,
                                                                  system=run["system"], alg=alg, basetype=basetype)
    data_max = max_of_arrays(data_max, data_max_new)
    vrfctn_members.append(vrfctn_members_new)

# Ende der Optimierung
dauer = time.time() - start
print(f"Die Optimierung dauerte {round(dauer, 2)} Sekunden.")


#-----------------------------------------------------------------------------------------------------------------------
# DEFINE LABELS OF PLOTS
plotted_data = [["h$_{struct}$", "[m]"], ["h$_{tot}$", "[m]"], ["GWP$_{struct}$", "[kg-CO$_2$-eq]"], ["GWP$_{tot}$", "[kg-CO$_2$-eq]"]]

# ADD LABELS, LEGEND, AXIS LIMITS AND GRID TO THE PLOTS
for idx, info in enumerate(plotted_data):
    plt.subplot(2, 2, idx + 1)
    plt.xlabel('l [m]', fontsize=12)
    plt.ylabel(info[0] + " " + info[1], fontsize=12)
    if idx % 2 == 0:
        plt.axis((min(lengths), max(lengths), 0, max(data_max[idx], data_max[idx+1])))
    else:
        plt.axis((min(lengths), max(lengths), 0, max(data_max[idx], data_max[idx-1])))
    plt.grid()

# # plot cross-section of members for verification
# for mem_group in vrfctn_members:
#     for i, mem in enumerate(mem_group[0]):
#         opt_and_plot.plot_section(mem.section)
#         plt.title(f'#{mem_group[1][i]}')

# SHOW FIGURE
plt.show()
