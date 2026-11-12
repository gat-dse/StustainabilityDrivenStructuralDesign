
#-----------------------------------------------------------------------------------------------------------------------
# FLOOR STRUCTURES (non load bearing layers: [product name, thickness or False for default, False])
# The name is used in the Excel file name and the result tables.


#--------------------------------------------------------------------------------------
#BODENAUFBAUTEN FUER MINDESTANFORDERUNGEN SCHALLSCHUTZ
#-------------------------------------------------------------------------------------
h_ins = 0.18
FLOORS_mind = {
    # solid reinforced concrete cross-section
    "massiv": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
               ["'Unterlagsboden Zement, 85 mm'", False, False],
               ["'Glaswolle'", 0.03, False]],



    # ribbed reinforced concrete cross-section (additional gravel)
    "Schuettung": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                   ["'Unterlagsboden Zement, 85 mm'", False, False],
                   ["'Glaswolle'", 0.03, False], ["'Kies gebrochen'", 0.06, False]],



    # solid wooden cross-section
    "Vollholz_Zement": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                 ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                 ["'Kies gebrochen'", 0.12, False]],

    "Vollholz_Anhydrit": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                 ["'Unterlagsboden Anhydrit, 60 mm'", False, False], ["'Glaswolle'", 0.03, False],
                 ["'Kies gebrochen'", 0.12, False]],


    # ribbed wooden cross-section (Hohlkastendecke)
    # For reaching REI60, Lignum 4.1, Table 433-2, Column G is applied. Thus Steinwolle
    # (180 mm) and Estrich (mind. 30mm) required as non load bearing layers.
    "Hohlkasten": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                   ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                   ["'Kies gebrochen'", 0.12, False], ["'Steinwolle'", h_ins, False]],
}
# insulation lies within the element -> subtract from the total height of the floor structure
FLOOR_H_CORRECTION = {"Hohlkasten": h_ins}



#--------------------------------------------------------------------------------------
#BODENAUFBAUTEN FUER ERHOEHTE ANFORDERUNGEN SCHALLSCHUTZ
#-------------------------------------------------------------------------------------
FLOORS_erh = {
    # solid reinforced concrete cross-section
    "massiv": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
               ["'Unterlagsboden Zement, 85 mm'", False, False],
               ["'Glaswolle'", 0.03, False]],
    # ribbed reinforced concrete cross-section (additional gravel)
    "Schuettung": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                   ["'Unterlagsboden Zement, 85 mm'", False, False],
                   ["'Glaswolle'", 0.03, False], ["'Kies gebrochen'", 0.06, False]],
    # solid wooden cross-section
    "Vollholz": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                 ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                 ["'Kies gebrochen'", 0.12, False]],
    # ribbed wooden cross-section (Hohlkastendecke)
    # For reaching REI60, Lignum 4.1, Table 433-2, Column G is applied. Thus Steinwolle
    # (180 mm) and Estrich (mind. 30mm) required as non load bearing layers.
    "Hohlkasten": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                   ["'Unterlagsboden Zement, 85 mm'", False, False], ["'Glaswolle'", 0.03, False],
                   ["'Kies gebrochen'", 0.12, False], ["'Steinwolle'", h_ins, False]],
}
# insulation lies within the element -> subtract from the total height of the floor structure
FLOOR_H_CORRECTION = {"Hohlkasten": h_ins}

