# TEST IF EPDs ARE PROPERLY CHOSEN
# define database
database_name = "database_260304.db"

connection = sqlite3.connect(database_name)
cursor = connection.cursor()

to_plot = []
# _____________________________________________________________________________________________________________________
# check Glued laminated timber
mat_name = ["'Glue_laminated_timber'"]
# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
inquiry = ("""
        SELECT PRO_ID FROM products
        WHERE DENSITY IS NOT NULL
        AND MECH_PROP IS NOT NULL
        AND Statistik = 1 
        AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
        AND "SOURCE" NOT LIKE '%Ecoinvent%'
        AND "SOURCE" NOT LIKE '%KBOB%'
        AND "MATERIAL" LIKE """ + mat_name
           )
# inquiry = ("SELECT PRO_ID FROM products WHERE"
#            " material=" + mat_name)
cursor.execute(inquiry)
resultGLULAM = cursor.fetchall()
for i, prod_id in enumerate(resultGLULAM):
    prod_id_str = "'" + str(prod_id[0]) + "'"
    inquiry = ("""
            SELECT MECH_PROP FROM products
            WHERE  PRO_ID LIKE """ + prod_id_str
               )
    # inquiry = ("SELECT mech_prop FROM products WHERE"
    #            " PRO_ID=" + prod_id_str)
    cursor.execute(inquiry)
    resultGLULAM = cursor.fetchall()
    mech_propGLULAM = "'" + resultGLULAM[0][0] + "'"

# _____________________________________________________________________________________________________________________
# CHECK PLYWOOD
mat_name = ["'3- and 5-ply wood'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
inquiry = ("""
        SELECT PRO_ID FROM products
        WHERE DENSITY IS NOT NULL
        AND MECH_PROP IS NOT NULL
        AND Statistik = 1 
        AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
        AND "SOURCE" NOT LIKE '%Ecoinvent%'
        AND "SOURCE" NOT LIKE '%KBOB%'
        AND "MATERIAL" LIKE """ + mat_name
           )
# inquiry = ("SELECT PRO_ID FROM products WHERE"
#            " material=" + mat_name)
cursor.execute(inquiry)
result = cursor.fetchall()
for i, prod_id in enumerate(result):
    prod_id_str = "'" + str(prod_id[0]) + "'"
    inquiry = ("""
            SELECT MECH_PROP FROM products
            WHERE  PRO_ID LIKE """ + prod_id_str
               )
    # inquiry = ("SELECT mech_prop FROM products WHERE"
    #            " PRO_ID=" + prod_id_str)
    cursor.execute(inquiry)
    result = cursor.fetchall()
    mech_prop = "'" + result[0][0] + "'"

# _____________________________________________________________________________________________________________________
# CHECK Solid structural timber

mat_name = ["'Solid_structural_timber'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
inquiry = ("""
        SELECT PRO_ID FROM products
        WHERE DENSITY IS NOT NULL
        AND MECH_PROP IS NOT NULL
        AND Statistik = 1 
        AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
        AND "SOURCE" NOT LIKE '%Ecoinvent%'
        AND "SOURCE" NOT LIKE '%KBOB%'
        AND "MATERIAL" LIKE """ + mat_name
           )
# inquiry = ("SELECT PRO_ID FROM products WHERE"
#            " material=" + mat_name)
cursor.execute(inquiry)
result = cursor.fetchall()
for i, prod_id in enumerate(result):
    prod_id_str = "'" + str(prod_id[0]) + "'"
    inquiry = ("""
            SELECT MECH_PROP FROM products
            WHERE  PRO_ID LIKE """ + prod_id_str
               )
    # inquiry = ("SELECT mech_prop FROM products WHERE"
    #            " PRO_ID=" + prod_id_str)
    cursor.execute(inquiry)
    result = cursor.fetchall()
    mech_prop = "'" + result[0][0] + "'"

# _____________________________________________________________________________________________________________________
# CHECK ready mixed concrete


mat_name = ["'ready_mixed_concrete'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
inquiry = ("""
        SELECT PRO_ID FROM products
        WHERE DENSITY IS NOT NULL
        AND MECH_PROP IS NOT NULL
        AND Statistik = 1 
        AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
        AND "SOURCE" NOT LIKE '%Ecoinvent%'
        AND "SOURCE" NOT LIKE '%KBOB%'
        AND "MATERIAL" LIKE """ + mat_name
           )
# inquiry = ("SELECT PRO_ID FROM products WHERE"
#            " material=" + mat_name)
cursor.execute(inquiry)
result = cursor.fetchall()
for i, prod_id in enumerate(result):
    prod_id_str = "'" + str(prod_id[0]) + "'"
    inquiry = ("""
            SELECT MECH_PROP FROM products
            WHERE  PRO_ID LIKE """ + prod_id_str
               )
    # inquiry = ("SELECT mech_prop FROM products WHERE"
    #            " PRO_ID=" + prod_id_str)
    cursor.execute(inquiry)
    result = cursor.fetchall()
    mech_prop = "'" + result[0][0] + "'"
mat_name = ["'Glue_laminated_timber'", "'3- and 5-ply wood'", "'Solid_structural_timber'","'ready_mixed_concrete'"]

# Wählt alle EPDs vom Material "mat-name" (z.B. ready mixed concrete), welche sich gem. Spalte Statistik zwischen dem 10% und 90% Quantil befindet. Wo Source = Betonsortenrechenr, Ecoinvent oder KBOB ist, wird die Zeile nicht gewählt.
inquiry = ("""
        SELECT PRO_ID FROM products
        WHERE DENSITY IS NOT NULL
        AND MECH_PROP IS NOT NULL
        AND Statistik = 1 
        AND "SOURCE" NOT LIKE '%Betonsortenrechner%'
        AND "SOURCE" NOT LIKE '%Ecoinvent%'
        AND "SOURCE" NOT LIKE '%KBOB%'
        AND "MATERIAL" LIKE """ + mat_name
           )
# inquiry = ("SELECT PRO_ID FROM products WHERE"
#            " material=" + mat_name)
cursor.execute(inquiry)
result = cursor.fetchall()
for i, prod_id in enumerate(result):
    prod_id_str = "'" + str(prod_id[0]) + "'"
    inquiry = ("""
            SELECT MECH_PROP FROM products
            WHERE  PRO_ID LIKE """ + prod_id_str
               )
    # inquiry = ("SELECT mech_prop FROM products WHERE"
    #            " PRO_ID=" + prod_id_str)
    cursor.execute(inquiry)
    result = cursor.fetchall()
    mech_prop = "'" + result[0][0] + "'"