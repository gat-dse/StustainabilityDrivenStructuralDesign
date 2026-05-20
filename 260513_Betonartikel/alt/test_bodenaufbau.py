# file contains code for verification of co2 calculation for bodenaufbau


# IMPORT
import create_dummy_database  # file for creating a "dummy database", as long as no real database is available
import struct_analysis  # file with code for structural analysis
import struct_optimization_2D
import struct_optimization  # file with code for structural optimization
#import matplotlib.pyplot as plt
import plot_datasets  # file with code for structural optimization
import matplotlib.pyplot as plt

# INPUT
database_name = "database_260506.db"  # define database name

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


for idx, layer in enumerate(bodenaufbau_rc.layers):
    print("Index:", idx)
    print("Schicht:", layer.name)
    print("Amortisationszeit:", layer.lifespan)

print("co2 ", bodenaufbau_rc.co2)
print("co2_a", bodenaufbau_rc.co2_a)