# file contains code for verification of members with wooden cross-sections


# IMPORT
import create_dummy_database  # file for creating a "dummy database", as long as no real database is available
import struct_analysis  # file with code for structural analysis
import struct_optimization_2D
import struct_optimization  # file with code for structural optimization
#import matplotlib.pyplot as plt
import plot_datasets  # file with code for structural optimization
import matplotlib.pyplot as plt
import pandas as pd

# INPUT
# create dummy-database
database_name = "database_260506.db"  # define database name
#create_dummy_database.create_database(database_name)  # create database

# create material for reinforced concrete cross-section, derive corresponding design values
concrete1 = struct_analysis.ReadyMixedConcrete("'C25/30'", database_name)  # create a Concrete material object
concrete1.get_design_values()
rebar1 = struct_analysis.SteelReinforcingBar("'B500B'", database_name)  # create a Concrete material object
rebar1.get_design_values()

# create reinforced concrete rectangular cross-section
section = struct_analysis.RectangularConcrete(concrete1, rebar1, 1.0, 0.24, 0.012, 0.15, 0.01, 0.15, 0.01, 0.15, 0.02, 0.15, 0.0, 0.15, 0)

# create floor structure for solid concrete cross-section
bodenaufbau = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                                 ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False]]
bodenaufbau_rc = struct_analysis.FloorStruc(bodenaufbau, database_name)

requirements = struct_analysis.Requirements()

# define loads on member
g2k = 0.75e3  # n.t. Einbauten
qk = 2e3  # Nutzlast

# define service limit state criteria
req = struct_analysis.Requirements()

length= 5


# create slab system
system = struct_analysis.BeamSimpleSup(length)


# create rc member
member = struct_analysis.Member1D(section, system, bodenaufbau_rc, requirements, g2k, qk)

opt_section = struct_optimization.get_optimized_section(member, "ENV", "GWP", 50)

# Import the function from your module
from class_to_excel_2 import member1d_to_dataframe

# Convert the single optimized section to the vertical DataFrame format
df_vertical = member1d_to_dataframe(opt_section)

print(df_vertical)

data = {
    "Height": [opt_section.h],
    "GWP": [opt_section.co2],
    "Material": [opt_section.co2_concrete],
    "Reinforcement_Layout": [ opt_section.bw],
}

df_summary = pd.DataFrame(data)

print(data)


#print("Kriechzahl creep_coef= ", opt_section.concrete_type.creep_coef)
#print("Kriechzahl phi= ", opt_section.phi)
#print("QS-Hoehe opt section = ", opt_section.h)
#print("GWP opt section = ", opt_section.co2)
#print("GWP bodenaufbau = ", bodenaufbau_rc.co2)
#print("GWP bodenaufbau mit amortisationszeit = ", bodenaufbau_rc.co2_a)
#print("GWP QS + Bodenaufbau in kg/m2= ", opt_section.co2 + bodenaufbau_rc.co2)

#print("GWP QS + Bodenaufbau pro Lebensdauer inkl. Ersatz in kg/m2 = ", opt_section.co2 + bodenaufbau_rc.co2_a)


#print("Mindestbewehrung as in m2/m' = ", opt_section.as_min)

#print("mu_max= ", round(section.mu_max,2))
#print("alpha_m: ",system.alpha_m)
#print("mkd_n, mkd_p = ", member.mkd_n, member.mkd_p)


#print("mu_min= ", round(section.mu_min,2))


#print("Bewehrungslayout = ", opt_section.bw[0][0])
#print("Bewehrungs-QS = ", opt_section.a_s_stat)

#print("mr_p =", opt_section.mr_p)
#print("x/d =", opt_section.x_p/opt_section.d)
#print("d =", opt_section.d)
#print("hmin =", opt_section.hmin_c)


#print("GWP-Bewehrung für QS pro m2 = ", opt_section.co2_rebar, "kgCO2-eq/m2")
#print("GWP_Bewehrung für Material pro Tonne = ", opt_section.rebar_type.GWP*1e3, "kgCO2-eq/t")
#print("GWP-Beton für QS pro m2 = ", opt_section.co2_concrete, "kgCO2-eq/m2")
#print("GWP-Beton für Material pro Tonne = ", opt_section.concrete_type.GWP*1e3, "kgCO2-eq/t")



# # # plot cross-section of members for verification
vrfctn_member = plot_datasets.plot_section(opt_section)

# SHOW FIGURE
plt.show()

print()