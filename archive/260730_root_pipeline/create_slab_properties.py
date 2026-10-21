# file creates a dummy database for testing the structure analysis code
# units: [m], [kg], [s], [N], [CHF]
import sqlite3


def create_database_slab(database_name):
    # create or open database sustainability
    connection = sqlite3.connect(database_name)

    # create cursor object
    cursor = connection.cursor()

    # delete existing products table
    try:
        cursor.execute("""DROP TABLE slab_properties;""")
    except:
        pass

    # create table for products data
    sql_command = """
    CREATE TABLE slab_properties ( 
    NAME TEXT, 
    RAENDER TEXT, 
    LX FLOAT, 
    LY FLOAT, 
    MX_POS FLOAT,
    MY_POS FLOAT,
    MX_NEG FLOAT,
    MY_NEG FLOAT,
    V_POS FLOAT,
    V_NEG FLOAT,
    W FLOAT,
    F FLOAT);"""
    cursor.execute(sql_command)

    # fill slab properties into db

    #Definitionen:
    #4-S: 4-Seitig auf Wänden gelagert
    #4-P: 4-Eckig auf Stützen gelagert
    #LL-frei: Liniengelagert nicht in Wand eingespannt → keine Durchlaufwirkung
    # LL-eingespannt: Liniengelagert eingespannt → Durchlaufwirkung

    """
    entries = [
        ("4S_3x3", "LL-frei", 3, 3, 0.04244, 0, 0.04244, 0, 0.30633, 0.30633, 0.00394, 0),
        ("4S_5x5", "LL-frei", 5, 5, 0.04296, 0, 0.04296, 0, 0.3206, 0.30633, 0.00391, 0),
        ("4S_6x6", "LL-frei", 6, 6, 0.042944, 0, 0.042944, 0, 0.3235, 0.3235, 0.00345, 0),
        ("4S_7x7", "LL-frei", 7, 7, 0.04298, 0, 0.04298, 0, 0.326, 0.326, 0.003945, 0),
        ("4S_8x8", "LL-frei", 8, 8, 0.043047, 0, 0.043047, 0, 0.3275, 0.3275, 0.00393, 0),
        ("4S_10x10", "LL-frei", 10, 10, 0.04304, 0, 0.04304, 0, 0.3297, 0.3297, 0.003945, 0)
    ]
    """
    entries = [
        ("4S_3x3", "LL-eingespannt", 3.0, 3.0, 0.01899, -0.04735, 0.01899, -0.04735, 0.37815, 0.37815, 0.00123, 0.0),
        ("4S_3x3", "LL-frei", 3.0, 3.0, 0.04395, 0.0, 0.04395, 0.0, 0.31047, 0.31047, 0.00355, 0.0),
        ("4P_3x3", "PL-eingespannt", 3.0, 3.0, 0.04555, -0.16139, 0.04555, -0.16139, 0.49028, 0.49028, 0.00339, 0.0),
        ("4P_3x3", "drop_beam", 3.0, 3.0, 0.02144, -0.06938, 0.02144, -0.06938, 0.23743, 0.23743, 0.00159, 0.0),

        ("4S_5x5", "LL-eingespannt", 5.0, 5.0, 0.02003, -0.04989, 0.02003, -0.04989, 0.40887, 0.40887, 0.00121, 0.0),
        ("4S_5x5", "LL-frei", 5.0, 5.0, 0.04419, 0.0, 0.04419, 0.0, 0.32341, 0.32341, 0.00367, 0.0),
        ("4P_5x5", "PL-eingespannt", 5.0, 5.0, 0.04388, -0.21449, 0.04388, -0.21449, 0.91956, 0.91956, 0.00326, 0.0),
        ("4P_5x5", "drop_beam", 5.0, 5.0, 0.01294, -0.05988, 0.01294, -0.05988, 0.28522, 0.28522, 0.00096, 0.0),

        ("4S_6x6", "LL-eingespannt", 6.0, 6.0, 0.02021, -0.05030, 0.02021, -0.05030, 0.41476, 0.41476, 0.00123, 0.0),
        ("4S_6x6", "LL-frei", 6.0, 6.0, 0.04410, 0.0, 0.04410, 0.0, 0.32589, 0.32589, 0.00374, 0.0),
        ("4P_6x6", "PL-eingespannt", 6.0, 6.0, 0.03858, -0.24001, 0.03858, -0.24001, 1.14284, 1.14284, 0.00289, 0.0),
        ("4P_6x6", "drop_beam", 6.0, 6.0, 0.00999, -0.05645, 0.00999, -0.05645, 0.29926, 0.29926, 0.00074, 0.0),

        ("4S_7x7", "LL-eingespannt", 7.0, 7.0, 0.02032, -0.05058, 0.02032, -0.05058, 0.41970, 0.41970, 0.00123, 0.0),
        ("4S_7x7", "LL-frei", 7.0, 7.0, 0.04403, 0.0, 0.04403, 0.0, 0.32805, 0.32805, 0.00377, 0.0),
        ("4P_7x7", "PL-eingespannt", 7.0, 7.0, 0.04112, -0.25637, 0.04112, -0.25637, 1.34561, 1.34561, 0.00298, 0.0),
        ("4P_7x7", "drop_beam", 7.0, 7.0, 0.00894, 0.05256, 0.00894, 0.05256, 0.30711, 0.30711, 0.00065, 0.0),

        ("4S_8x8", "LL-eingespannt", 8.0, 8.0, 0.02039, -0.05076, 0.02039, -0.05076, 0.42261, 0.42261, 0.00122, 0.0),
        ("4S_8x8", "LL-frei", 8.0, 8.0, 0.04396, 0.0, 0.04396, 0.0, 0.32926, 0.32926, 0.00378, 0.0),
        ("4P_8x8", "PL-eingespannt", 8.0, 8.0, 0.03933, -0.27067, 0.03933, -0.27067, 1.54602, 1.54602, 0.00289, 0.0),
        ("4P_8x8", "drop_beam", 8.0, 8.0, 0.00763, -0.04919, 0.00763, -0.04919, 0.31290, 0.31290, 0.00055, 0.0),

        (
        "4S_10x10", "LL-eingespannt", 10.0, 10.0, 0.02047, -0.05096, 0.02047, -0.05096, 0.42687, 0.42687, 0.00123, 0.0),
        ("4S_10x10", "LL-frei", 10.0, 10.0, 0.04383, 0.0, 0.04383, 0.0, 0.33112, 0.33112, 0.00382, 0.0),
        (
        "4P_10x10", "PL-eingespannt", 10.0, 10.0, 0.04071, -0.29888, 0.04071, -0.29888, 2.05346, 2.05346, 0.00293, 0.0),
        ("4P_10x10", "drop_beam", 10.0, 10.0, 0.00625, -0.04443, 0.00625, -0.04443, 0.34070, 0.34070, 0.00045, 0.0),

        (
        "4S_12x12", "LL-eingespannt", 12.0, 12.0, 0.02051, -0.05107, 0.02051, -0.05107, 0.42932, 0.42932, 0.00123, 0.0),
        ("4S_12x12", "LL-frei", 12.0, 12.0, 0.04373, 0.0, 0.04373, 0.0, 0.33216, 0.33216, 0.00384, 0.0),
        (
        "4P_12x12", "PL-eingespannt", 12.0, 12.0, 0.04061, -0.31823, 0.04061, -0.31823, 2.44778, 2.44778, 0.00290, 0.0),
        ("4P_12x12", "drop_beam", 12.0, 12.0, 0.00522, -0.03993, 0.00522, -0.03993, 0.34300, 0.34300, 0.00037, 0.0),

        (
        "4S_16x16", "LL-eingespannt", 16.0, 16.0, 0.02056, -0.05119, 0.02056, -0.05119, 0.43266, 0.43266, 0.00123, 0.0),
        ("4S_16x16", "LL-frei", 16.0, 16.0, 0.04360, 0.0, 0.04360, 0.0, 0.33365, 0.33365, 0.00387, 0.0),
        (
        "4P_16x16", "PL-eingespannt", 16.0, 16.0, 0.04047, -0.34909, 0.04047, -0.34909, 3.22987, 3.22987, 0.00287, 0.0),
        ("4P_16x16", "drop_beam", 16.0, 16.0, 0.00392, -0.03342, 0.00392, -0.03342, 0.34558, 0.34558, 0.00028, 0.0),
    ]

    for entry in entries:
        sql_command = """INSERT INTO slab_properties (NAME, RAENDER, LX, LY, MX_POS, MX_NEG, MY_POS, MY_NEG, V_POS, V_NEG, W, F )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        cursor.execute(sql_command, entry)



    # safe changes in database
    connection.commit()

    # close database
    connection.close()


database_name = "slab_properties.db"
create_database_slab(database_name)



import sqlite3
from tabulate import tabulate  # pip install tabulate (optional, für schöne Ausgabe)

def show_database_contents(database_name):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()


    cursor.execute("SELECT * FROM slab_properties")
    rows = cursor.fetchall()

    # Spaltennamen holen
    column_names = [description[0] for description in cursor.description]

    # Ausgabe als Tabelle
    print(tabulate(rows, headers=column_names, tablefmt="grid"))

    connection.close()

# Aufruf
show_database_contents("slab_properties.db")