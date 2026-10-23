import sqlite3  # import modul for SQLite
import struct_analysis  # file with code for structural analysis
import struct_optimization # file with code for structural optimization
import struct_optimization_RCrib_cont  # file with code for structural optimization
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon
from scipy.interpolate import interp1d
import class_to_excel
import class_to_excel_2


import pandas as pd
from scipy.spatial import ConvexHull

# KBOB rows: only they have a "KBOB ID-Nr." (empty for EPD rows, NULL in the DB); every other row counts as EPD
KBOB_CONDITION = "(\"KBOB ID-Nr.\" IS NOT NULL)"

def source_filter(basetype):
    # SQL fragment selecting the data basis: product EPDs or generic KBOB values
    if basetype == "kbob":
        return f" AND {KBOB_CONDITION} AND Man_Ausschluss = 1 AND CAST(Total_GWP AS REAL) > 0 "
    elif basetype == "epd":
        return f" AND NOT {KBOB_CONDITION} AND ValidEPD = 1 AND Man_Ausschluss = 1 "
    raise ValueError(f"basetype must be 'epd' or 'kbob', got {basetype}")

# To see the old version, run git show 36ba32b:Workflow/opt_and_plot.py (around lines 80–205).
def get_products_by_gwp(cursor, material, mech_prop, basetype):
    # returns [(PRO_ID, GWP)] of all products of a material, sorted ascending by GWP
    # material: LIKE pattern for column MATERIAL; mech_prop: required MECH_PROP or None (any MECH_PROP)
    # condition on MECH_PROP: a given strength class (e.g. 'B500B') or, for None, any product that has one
    mech_cond = "MECH_PROP = ?" if mech_prop is not None else "MECH_PROP IS NOT NULL"
    # SQL query, line by line:
    #   SELECT PRO_ID ...          only the product IDs are needed, the material classes read the rest themselves
    #   "MATERIAL" LIKE ?          material name, '?' is filled with `material` (allows '%' wildcards)
    #                              (old plywood query: outer WHERE without material filter)
    #   DENSITY IS NOT NULL        skip products without density: the material classes need it for the mass
    #                              (volume * density) and float(None) would crash
    #   mech_cond                  strength class condition from above
    #   source_filter(basetype)    EPD or KBOB rows, see source_filter() (old plywood query: no Man_Ausschluss)
    #   ORDER BY GWP, PRO_ID       sort ascending by GWP: first row = lowest, last row = highest GWP;
    #                              PRO_ID decides between equal GWP values, so the result is always the same
    #                              (old: no ORDER BY -> low/high swapped, ties gave >2 rows)
    inquiry = ("""
            SELECT PRO_ID, CAST(Total_GWP AS REAL) FROM products
            WHERE "MATERIAL" LIKE ?
              AND DENSITY IS NOT NULL
              AND """ + mech_cond + source_filter(basetype) + """
            ORDER BY CAST(Total_GWP AS REAL), PRO_ID
            """
    )
    params = [material] if mech_prop is None else [material, mech_prop]  # values for the '?' placeholders, in order
    cursor.execute(inquiry, params)  # run the query; the parameters are inserted safely by sqlite3
    result = cursor.fetchall()  # rows are tuples (PRO_ID, GWP), sorted by GWP
    if not result:  # no matching product: clear message (old: IndexError)
        raise ValueError(f"no product found for material {material}, mech_prop {mech_prop}, basetype {basetype}")
    return result


def get_low_high_prod_ids(cursor, material, mech_prop, basetype):
    # returns unique prod_id strings of the products with lowest and highest GWP of a material
    # (only one entry if min == max, e.g. a single KBOB product)
    result = [row[0] for row in get_products_by_gwp(cursor, material, mech_prop, basetype)]
    prod_ids = []  # collects the selected IDs as SQL strings, e.g. "'123'"
    for prod_id in (result[0], result[-1]):  # lowest and highest GWP (old: result[1] -> IndexError with 1 product)
        prod_id_str = "'" + str(prod_id) + "'"  # quote the ID, the material classes put it directly into their SQL
        if prod_id_str not in prod_ids:  # skip the duplicate if min == max (e.g. only one KBOB rebar)
            prod_ids.append(prod_id_str)  # (old: 2 identical sections)
    prod_ids.sort(key=lambda x: int(x.strip("'")))  # sort by PRO_ID (as a number, without quotes): same section
                                                    # order as the old queries, which returned rows in PRO_ID order
    return prod_ids  # 1 or 2 IDs; the caller builds one cross-section per ID

def get_mean_prod_id(cursor, materials, mech_prop, basetype):
    # returns the prod_id string of the product whose GWP is closest to the mean GWP of all products of the
    # material(s) (same products as get_low_high_prod_ids; equal distance: the lower GWP wins)
    # materials: one LIKE pattern or a list of them (pooled, e.g. glulam and solid timber of one run)
    if isinstance(materials, str):
        materials = [materials]
    # pooled list sorted by GWP (then PRO_ID), so that min() below returns the lower GWP for equal distances
    products = sorted((row for material in materials for row in get_products_by_gwp(cursor, material, mech_prop,
                                                                                    basetype)),
                      key=lambda row: (row[1], row[0]))
    mean = sum(gwp for _, gwp in products) / len(products)
    prod_id = min(products, key=lambda row: abs(row[1] - mean))[0]
    return "'" + str(prod_id) + "'"

# PLOT DATASETS OF MEMBERS WITH DEFINED CROSS_SECTIONS AND VARIED MATERIALS
# ----------------------------------------------------------------------------------------------------------------------
def plot_dataset(lengths, database_name, criteria, optima, floorstruc, requirements, crsec_type, mat_names,
                 g2k=0.75, qk=2.0, max_iter=100, idx_vrfctn=-1, system = "Simple Beam", alg="basinhoppin",
                 basetype="epd", results=None, file_tag="", mean_gwp=False):
    # results: optional list; one dict per optimized member (incl. infeasible spans with member=None) is appended
    # file_tag: optional suffix of the Excel file name (avoids overwriting when runs share the same name)
    # mean_gwp: True -> one additional "mean section" (EPD only): main material (all mat_names together), rebar
    #           rsp. board are the products closest to the mean GWP (KBOB: one product per material, no mean)

    if idx_vrfctn == -1:
        idx_vrfctn = random.randint(0, len(lengths)-1) #if idx_verfctn isnt specified, pick a random

    # GENERATE INITIAL CROSS-SECTIONS
    # Search database (table products, attribute material) for products
    # get prod_id of relevant materials from database and create initial cross-section for each product
    to_plot = []
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    products = []  # (prod_id string, is_mean): every product of all materials of the run
    for mat_name in mat_names:
        # Wählt alle EPDs von einem Material -> "mat-name" (z.B. ready mixed concrete)
        inquiry = ("""
                SELECT PRO_ID FROM products
                WHERE DENSITY IS NOT NULL                
                AND MECH_PROP IS NOT NULL
                AND "MATERIAL" LIKE """ + mat_name + source_filter(basetype)
        )
        # inquiry = ("SELECT PRO_ID FROM products WHERE"
        #            " material=" + mat_name)
        cursor.execute(inquiry)
        products += [("'" + str(row[0]) + "'", False) for row in cursor.fetchall()]
    # mean section: the product closest to the mean GWP of all these products (all materials of the run together)
    if mean_gwp and basetype == "epd":
        products.append((get_mean_prod_id(cursor, [m.strip("'") for m in mat_names], None, basetype), True))
    for prod_id_str, is_mean in products:
        inquiry = ("""
                SELECT MECH_PROP FROM products
                WHERE  PRO_ID LIKE """ + prod_id_str
        )
        # inquiry = ("SELECT mech_prop FROM products WHERE"
        #            " PRO_ID=" + prod_id_str)
        cursor.execute(inquiry)
        result = cursor.fetchall()
        raw_val = result[0][0].strip()

        #Fall es ein Holz-Querschnitt ist und mech_prop "GL" enthalten ist:
        #Prüfen, ob mech_prop mit "h" oder "c" endet. Falls nicht, wird jeweils Festigkeit für "c" gewählt (konservativ). z.B. für GL30 --> Gl30c
        if raw_val.startswith('GL'):
            if not raw_val.endswith(('h','c')):
                raw_val += 'c'
        mech_prop = f"'{raw_val}'"


        if crsec_type == "wd_rec":
            # create a Wood material object
            timber = struct_analysis.Wood(mech_prop, database_name, prod_id_str)
            timber.get_design_values()
            # create initial wooden rectangular cross-section
            section_0 = struct_analysis.RectangularWood(timber, 1.0, 0.1, xi=0.02)
            # add section to content-definition of plot-line
            line_i = [section_0, floorstruc, is_mean]
            to_plot.append(line_i)

        elif crsec_type == "rc_rec":
            # create a Concrete material object
            concrete = struct_analysis.ReadyMixedConcrete(mech_prop, database_name, prod_id=prod_id_str)
            concrete.get_design_values()
            # search database for rebar material of type B500B with lowest and highest emissions
            # (mean section: the rebar closest to the mean GWP)
            if is_mean:
                rebar_prod_ids = [get_mean_prod_id(cursor, 'Steel_reinforcing_bar', 'B500B', basetype)]
            else:
                rebar_prod_ids = get_low_high_prod_ids(cursor, 'Steel_reinforcing_bar', 'B500B', basetype)
            for rebar_prod_id in rebar_prod_ids:
                # create a rebar material object with mech prop B500B and low rsp high emission values
                rebar = struct_analysis.SteelReinforcingBar("'B500B'", database_name, prod_id=rebar_prod_id)
                # create initial cross-section
                section_0 = struct_analysis.RectangularConcrete(concrete, rebar, 1.0, 0.20,
                                                                0.014, 0.15, 0.008, 0.15, 0.008, 0.15, 0.008, 0.15,
                                                                0, 0.15, 2)
                # add section to content-definition of plot-line
                to_plot.append([section_0, floorstruc, is_mean])

        elif crsec_type == "rc_rib":
            # create a Concrete material object
            concrete = struct_analysis.ReadyMixedConcrete(mech_prop, database_name, prod_id=prod_id_str)
            concrete.get_design_values()
            # search database for rebar material of type B500B with lowest and highes emissions
            # (mean section: the rebar closest to the mean GWP)
            if is_mean:
                rebar_prod_ids = [get_mean_prod_id(cursor, 'Steel_reinforcing_bar', 'B500B', basetype)]
            else:
                rebar_prod_ids = get_low_high_prod_ids(cursor, 'Steel_reinforcing_bar', 'B500B', basetype)
            for rebar_prod_id in rebar_prod_ids:
                # create a rebar material object with mech prop B500B and low rsp high emission values
                rebar = struct_analysis.SteelReinforcingBar("'B500B'", database_name, prod_id=rebar_prod_id)
                # create initial cross-section
                section_0 = struct_analysis.RibbedConcrete(concrete, rebar, 4, 1.0, 0.15, 0.3, 0.18, 0.008, 0.15, 0.008, 0.15, 0.018, 5, 0.008, 0.15, 2, 1, 2.0, 0.02, 0.03, 0.15)
                # add section to content-definition of plot-line
                to_plot.append([section_0, floorstruc, is_mean])

        elif crsec_type == "wd_rib":
            # create a Wood material object
            timber1 = struct_analysis.Wood(mech_prop, database_name, prod_id=prod_id_str)  # create a Wood material object
            timber1.get_design_values()

            # search database for timber board material (CLT) with lowest and highest emissions
            # (mean section: the board closest to the mean GWP)
            if is_mean:
                clt_prod_ids = [get_mean_prod_id(cursor, '%3_and_5_plywood%', None, basetype)]
            else:
                clt_prod_ids = get_low_high_prod_ids(cursor, '%3_and_5_plywood%', None, basetype)
            for clt_prod_id in clt_prod_ids:
                # create a timber material object in timber board (CLT, C24) with low rsp high emission values
                clt = struct_analysis.Wood("'C24'", database_name, prod_id=clt_prod_id)
                clt.get_design_values()
                # create initial cross-section
                section_0 = struct_analysis.RibWood(timber1, clt, clt, 4, 0.12, 0.22, 0.625,
                                                    0.027, 0.027)
                # add section to content-definition of plot-line
                to_plot.append([section_0, floorstruc, is_mean])

        else:
            print("cross-section type is not defined inside function plot_dataset()")



    # ANALYSIS AND OPTIMIZATION OF CROSS-SECTIONS
    member_list = []
    legend = []
    # create plot data
    for i in to_plot:
        for criterion in criteria:
            for optimum in optima:
                # wd_rib: t2 is fixed, t3 has two fixed cases (T_KANDIDATEN_WDRIB) -> optimize once per case.
                # Every other section type runs a single pass with no fixed parameters.
                if crsec_type == "wd_rib":
                    fixed_param_cases = [{"t3": t3_case} for t3_case in struct_optimization.T_KANDIDATEN_WDRIB]
                else:
                    fixed_param_cases = [{}]
                for fixed_params in fixed_param_cases:
                    members = []
                    for length in lengths:
                        if system == "Simple Beam":
                            sys = struct_analysis.BeamSimpleSup(length)
                        elif system == "Two span 1D 1D":
                            sys = struct_analysis.BeamTwoSpan(length)
                        elif system == "Continuous 1D":
                            sys =struct_analysis.BeamContinuousSupEl(length)
                        else:
                            print("System unknown; Simple Beam used")
                            sys = struct_analysis.BeamSimpleSup(length)
                        section0 = i[0]
                        floorstruc = i[1]
                        member0 = struct_analysis.Member1D(section0, sys, floorstruc, requirements, g2k, qk)

                        if system == "Continuous 1D" and crsec_type == "rc_rib":
                            opt_section = struct_optimization_RCrib_cont.get_optimized_section(member0, criterion, optimum,
                                                                                               max_iter,alg)
                        else:
                            opt_section = struct_optimization.get_optimized_section(member0, criterion, optimum, max_iter, alg,
                                                                                     fixed_params=fixed_params)

                        #Handle infeasible solutions (e.g. span too large for wd_rec crosssection)
                        if opt_section is None:
                            print(f"Warning: no feasible {crsec_type} section for span {length} m {fixed_params} "
                                  f"-> no section in output")
                            members.append(None)
                            opt_member = None
                        else:
                            opt_member = struct_analysis.Member1D(opt_section, sys, floorstruc, requirements, g2k, qk)
                            members.append(opt_member)

                        if results is not None:
                            results.append({"member": opt_member, "section_0": section0, "length": length,
                                            "criterion": criterion, "optimum": optimum,
                                            "t3": fixed_params.get("t3"), "dataset": len(member_list),
                                            "mean_section": i[2]})
                    member_list.append(members)
                    if i[0].section_type[0:2] == "rc":
                        material_lg = i[0].concrete_type.mech_prop + " + " + i[0].rebar_type.mech_prop
                    elif i[0].section_type == "wd":
                        material_lg = i[0].wood_type.mech_prop
                    elif i[0].section_type == "wd_rib":
                        material_lg = i[0].wood_type_1.mech_prop
                    else:
                        material_lg = "error: section material is not defined"
                    legend.append([i[0].section_type, material_lg, criterion, optimum, floorstruc.name, fixed_params.get("t3"), basetype])

    # Infeasible solutions stay as None in member_list, so that member_list[i][j] still belongs to lengths[j].
    # (Removing them would shift the indices and zip(*...) would cut the envelopes of all materials to the
    # shortest list.) Envelopes are calculated per length over the feasible members only; lengths without any
    # feasible member are left out.
    members_per_length = [[mem for mem in col if mem is not None] for col in zip(*member_list)]
    idx_feasible = [j for j, mems in enumerate(members_per_length) if mems]
    lengths_filtered = [lengths[j] for j in idx_feasible]

    # CREATE DATA OF ENVELOPE AREA OF DATASET
    # subplot 1: structural height, subplot 2: total height, subplot 3: co2 of structure, subplot 4: total co2
    value_getters = [lambda mem: mem.section.h,
                     lambda mem: mem.section.h + mem.floorstruc.h_Floor,
                     lambda mem: mem.section.co2,
                     lambda mem: mem.section.co2 + mem.floorstruc.co2_Floor]
    values_min, values_max, values_mean = [], [], []
    for get_value in value_getters:
        per_length = [[get_value(mem) for mem in members_per_length[j]] for j in idx_feasible]
        values_min.append([min(values) for values in per_length])
        values_max.append([max(values) for values in per_length])
        values_mean.append([sum(values) / len(values) for values in per_length])

    # CREATE DATASET



    # PLOT DATASET TO FIGURE
    plt.rcParams.update({
        'font.family': 'Times New Roman'
    })


    plt.figure(1)
    data_max = [0, 0, 0, 0]
    vrfctn_members = [[], []]
    for i, members in enumerate(member_list):
        plotdata = [[], [], [], []]
        for j, mem in enumerate(members):
            if mem is None:  # no feasible section for lengths[j]
                continue
            plotdata[0].append(mem.section.h)

            plotdata[1].append(mem.section.h + mem.floorstruc.h_Floor)
            plotdata[2].append(mem.section.co2)
            plotdata[3].append(mem.section.co2 + mem.floorstruc.co2_Floor)
            if j == idx_vrfctn:
                vrfctn_members[0].append(mem)
                vrfctn_members[1].append(i)
        sec_typ, mat, cri, opt, floor_name, t3_val, base = legend[i]
        # set line color
        if sec_typ == "rc_rec" and system == "Simple Beam" and floor_name == "massiv":
            color = 'darkgreen'

        elif sec_typ == "rc_rec" and system == "Simple Beam" and floor_name == "Schuettung":
            color = 'darkolivegreen'

        elif sec_typ == "rc_rec" and system == "Continuous 1D" and floor_name == "Schuettung":
            color = 'olivedrab'

        elif sec_typ == "rc_rec" and system == "Simple Beam":
            color = 'darkgreen'

        elif sec_typ == "rc_rec" and system == "Continuous 1D":
            color = 'lightgreen'

        elif sec_typ == "wd_rec":
            color = 'saddlebrown'

        elif sec_typ == "rc_rib" and system == "Simple Beam":
            color = 'limegreen'

        elif sec_typ == "rc_rib" and system == "Continuous 1D" :
            color = 'yellow'

        elif sec_typ == "wd_rib":
            color = 'sandybrown'

        else:
            color = "k"

        # set linestyle
        if cri == "ULS":
            linestyle = "--"  # line style for ULS
        elif cri == "SLS1":
            linestyle = (0, (3, 1, 1, 1))  # line style for SLS1
        elif cri == "SLS2":
            linestyle = ":"  # line style for SLS2
        elif cri == "ENV":
            linestyle = "-"  # line style for ENV
        else:
            linestyle = (0, (1, 10))
        # set linewidth
        if opt == "h":
            linewidth = 0.5
        elif opt == "GWP":
            linewidth = 1.0
        else:
            linewidth = 0.1
        label = sec_typ + ", " + mat + ", " + cri + ", optimized for " + opt + ", " + base
        if t3_val is not None:
            label += f", t3={t3_val}"
        # plot data
        for idx, data in enumerate(plotdata):
            plt.subplot(2, 2, idx + 1)
            # prepare area
            coords = list(zip(lengths_filtered, values_max[idx])) + list(zip(lengths_filtered[::-1], values_min[idx][::-1]))
            # create a polygon from the coordinates
            polygon = Polygon(coords)
            # extract the x and y coordinates for plotting
            x, y = polygon.exterior.xy
            # plot area
            plt.fill(x, y, alpha=0.05, facecolor=color, edgecolor = color, linewidth = 1.5)
            # plot lines
            #plt.plot(lengths_filtered, data, color=color, linestyle=linestyle, linewidth=linewidth, label=label, alpha=0.2)
            data_max[idx] = max([data_max[idx]] + data)
            # # plot points of verification into graph
            # ver_x, ver_y = lengths_filtered[idx_vrfctn], data[idx_vrfctn]
            # plt.plot(ver_x, ver_y, 'o', color='black', markersize=2)
            # plt.annotate(f'#{i}', xy=(ver_x, ver_y),
            #              xytext=(ver_x + 0.05*lengths_filtered[-1], ver_y),
            #              arrowprops=dict(facecolor='black', shrink=0.2, width=0.2, headwidth=2, headlength=4),
            #              fontsize=9, color='black', va='center')
            plt.plot(lengths_filtered, values_mean[idx], color = color, linestyle = linestyle, linewidth = 1.5 )


    # create Excel sheets
    members_1d = [
        member
        for pair in member_list
        for member in pair
        if member is not None
    ]

    '''if crsec_type == "wd_rec":
        class_to_excel.members_to_excel(members_1d, "Members_wd_rec.xlsx", folder="Resultate")

    elif crsec_type == "rc_rec"and system == "Simple Beam":
        #class_to_excel.members_to_excel(members_1d, "Members_rc_rec.xlsx", folder="Resultate")
        if members_1d:
            floor_name = members_1d[0].floorstruc.name
            floor_name_clean = str(floor_name)
        else:
            floor_name_clean = "default"

        dynamic_filename = f"Members_rc_rec_{floor_name_clean}_2.xlsx"

        class_to_excel_2.members_to_excel2(members_1d, dynamic_filename, folder="Results")
        #class_to_excel_2.members_to_excel2(members_1d, "Members_rc_rec_2.xlsx", folder="Results")

    elif crsec_type == "rc_rib" and system == "Simple Beam":
        #class_to_excel.members_to_excel(members_1d, "Members_rc_rib.xlsx", folder="Resultate")
        class_to_excel_2.members_to_excel2(members_1d, "Members_rc_rib_2.xlsx", folder="Results")
    elif crsec_type == "rc_rec"and system == "Continuous 1D":
        #class_to_excel.members_to_excel(members_1d, "Members_rc_rec_cont.xlsx", folder="Resultate")
        class_to_excel_2.members_to_excel2(members_1d, "Members_rc_rec_cont_2.xlsx", folder="Results")
    elif crsec_type == "rc_rib" and system == "Continuous 1D":
        #class_to_excel.members_to_excel(members_1d, "Members_rc_rib_cont.xlsx", folder="Resultate")
        class_to_excel_2.members_to_excel2(members_1d, "Members_rc_rib_cont_2.xlsx", folder="Results")

    elif crsec_type == "rc_rec"and system == "Two span 1D 1D":
        #class_to_excel.members_to_excel(members_1d, "Members_rc_rec_2span.xlsx", folder="Resultate")
        class_to_excel_2.members_to_excel2(members_1d, "Members_rc_rec_2span_2.xlsx", folder="Results")


    elif crsec_type == "wd_rib":
        class_to_excel.members_to_excel(members_1d, "Members_wd_rib.xlsx", folder="Resultate")
    else:
        print("cross-section type is not defined inside function plot_dataset()")'''

    # 1. Dynamisch den Bodenaufbau (floor_name) auslesen, falls vorhanden
    if members_1d and hasattr(members_1d[0], 'floorstruc') and members_1d[0].floorstruc:
        floor_name = members_1d[0].floorstruc.name
        floor_name_clean = f"_{str(floor_name).replace(' ', '_').replace('/', '-')}"
    else:
        floor_name_clean = ""

    # 2. System-Suffix übersetzen (Kurzformen für den Dateinamen)
    system_mapping = {
        "Simple Beam": "_simple",
        "Continuous 1D": "_cont",
        "Two span 1D 1D": "_2span"
    }
    # Nimmt das Suffix aus dem Mapping, andernfalls wird der Systemname direkt (bereinigt) angehängt
    system_suffix = system_mapping.get(system, f"_{str(system).replace(' ', '_')}")

    # 3. Weiche für Export-Klasse und Ordner anhand des Präfixes ('wd' vs. alle anderen)
    # Use members_to_excel2 and folder 'Results' for all cross-section types (including wood 'wd')
    filename = f"Members_{crsec_type}{system_suffix}{floor_name_clean}_{basetype}{file_tag}.xlsx"
    class_to_excel_2.members_to_excel2(members_1d, filename, folder="Results")



    return data_max, vrfctn_members



# PLOT GEOMETRY OF SECTIONS
# ----------------------------------------------------------------------------------------------------------------------
def plot_section(section):
    # Create a figure and axis
    if section.section_type == "rc_rec":  # Rectangular Reinforced Concrete Cross-Section
        fig, ax, offset = plot_rectangle_with_dimensions(section.b, section.h, 'green', 'x')
        plot_rebars_long(ax, section, offset)
        # add stirrups to plot (if stirrups are defined)
        if section.bw_bg[0] > 0 and section.bw_bg[2] > 0:
            plot_stirrups(ax, section, offset)
        legend = (f'{section.concrete_type.mech_prop}, prod_ID:{section.concrete_type.prod_id} \n'
                  f'{section.rebar_type.mech_prop}, prod_ID:{section.rebar_type.prod_id} \n'
                  f'di_xo / s_xo = {section.bw[1][0]:.3f} / {section.bw[1][1]} \n'
                  f'di_xu / s_xu = {section.bw[0][0]:.3f} / {section.bw[0][1]} \n'
                  f'di_stir / s_stir / n = {section.bw_bg[0]} / {section.bw_bg[1]} / {section.bw_bg[2] }\n'
                  f'c_nom = {100*section.c_nom:.1f} cm \n'
                  f'x/d = {section.x_p/section.d:.2f} \n'
                  f'GWP = {section.co2:.0f} kg/m^2 \n'
                  f'UBP = {section.ubp:.0f} UBP/m^2 \n'
                  f'GE = {section.graue_energie:.0f} kWh/m^2')
    elif section.section_type == "wd_rec":  # Rectangular Wooden Cross-Section
        fig, ax, offset = plot_rectangle_with_dimensions(section.b, section.h, 'brown', '/')
        legend = (f'{section.wood_type.mech_prop}, prod_ID:{section.wood_type.prod_id} \n'
                  f'GWP = {section.co2:.0f} kg/m^2 \n'
                  f'UBP = {section.ubp:.0f} UBP/m^2 \n'
                  f'GE = {section.graue_energie:.0f} kWh/m^2')

    elif section.section_type == "rc_rib": #Betonrippenquerschnitte
        fig, ax, offset = plot_rib_with_dimensions(section.b, section.b_w, section.h, section.h_f, 'green', 'x')
        legend = (f'{section.concrete_type.mech_prop}, prod_ID:{section.concrete_type.prod_id} \n'
              f'length = {section.l0} \n'
              f'{section.rebar_type.mech_prop}, prod_ID:{section.rebar_type.prod_id} \n'
              f'di_r = {section.bw_r[0]:.3f} \n'
              f'di_xu / s_xu = {section.bw[0][0]:.3f} / {section.bw[0][1]} \n'
              #f'di_stir / s_stir / n = {section.bw_bg[0]} / {section.bw_bg[1]} / {section.bw_bg[2]}\n'
              f'di_xo / s_xo / n = {section.bw[1][0]:.3f} / {section.bw[1][1]} \n'
              f'di_x_w / n_x_w / n = {section.bw_r[0]:.3f} / {section.bw_r[1]} \n'
              f'c_nom = {100 * section.c_nom:.1f} cm \n'
              f'x/d = {section.x_p / section.d:.2f} \n'
              f'h, hf, hw, b, bw = {section.h:.2f}, {section.h_f:.2f}, {section.h_w:.2f}, {section.b:.2f}, {section.b_w:.2f} \n'
              f'GWP = {section.co2:.0f} kg/m^2 \n'
              f'UBP = {section.ubp:.0f} UBP/m^2 \n'
              f'GE = {section.graue_energie:.0f} kWh/m^2')

    elif section.section_type == "wd_rib": #Betonrippenquerschnitte
        fig, ax, offset = plot_wd_rib_with_dimensions(section.bw, section.h, section.b, section.t2, section.t3, 'brown', 'x')
        legend = (f'{section.wood_type_1.mech_prop}, prod_ID:{section.wood_type_1.prod_id} \n'
              f'length = {section.l0} \n'
              f'h, bw, b, t2, t3 = {section.h:.2f}, {section.bw:.2f}, {section.b:.2f}, {section.t2:.2f}, {section.t3:.2f} \n'
              f'GWP = {section.co2:.0f} kg/m^2 \n'
              f'UBP = {section.ubp:.0f} UBP/m^2 \n'
              f'GE = {section.graue_energie:.0f} kWh/m^2')

    else:
        print("no plot for specified section_type defined yet")
        fig, ax = plt.subplots()
        legend = f'no plot for section_type "{section.section_type}" defined yet'
    fig.text(0.01, 0.99, legend, ha='left', va='top', fontsize=9, color='black',
             bbox=dict(facecolor='lightgrey', edgecolor='black', boxstyle='round,pad=0.2'))


# Function to plot a rectangular cross-section with given dimensions
def plot_rectangle_with_dimensions(width, height, color='black', hatch='*', offset=0.1):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Define the rectangle with hatching (lower-left corner at (x, y), width, and height)
    rect = patches.Rectangle((offset, offset), width, height, linewidth=1, edgecolor=color, facecolor='none',
                             hatch=hatch, fill=False)

    # Add the rectangle to the plot
    ax.add_patch(rect)

    # Add dimension annotations
    ax.annotate(f'b = {width:.2f} m', xy=(offset + width / 2, 0.05), xytext=(offset + width / 2, 0.06), ha='center')
    ax.annotate(f'h = {height:.2f} m', xy=(0.02, offset + height / 2), xytext=(0.01, offset + height / 2),
                va='center', rotation='vertical')

    # Draw arrows for dimensions
    # ax.annotate('', xy=(0.1, 0.05), xytext=(0.1 + width, 0.05), arrowprops=dict(arrowstyle='|-|', color='black'))
    # ax.annotate('', xy=(0.05, 0.1), xytext=(0.05, 0.1 + height), arrowprops=dict(arrowstyle='|-|', color='black'))

    # Hide the x and y axes
    ax.axis('off')

    # Set the aspect of the plot to be equal
    ax.set_aspect('equal')

    # Set the limits of the plot
    ax.set_xlim(0, width+5*offset)
    ax.set_ylim(0, height+4*offset)

    return fig, ax, offset

def plot_rib_with_dimensions(b, bw, h, hf, color='black', hatch='*', offset=0.1):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Define the rectangle with hatching (lower-left corner at (x, y), width, and height)
    rect_flange = patches.Rectangle((offset, offset+h-hf), 2*b, hf, linewidth=1, edgecolor=color, facecolor='none',
                             hatch=hatch, fill=False)
    rect_rib1 = patches.Rectangle((offset+b/2-bw/2, offset), bw, h-hf, linewidth=1, edgecolor=color, facecolor='none',
                             hatch=hatch, fill=False)
    rect_rib2 = patches.Rectangle((offset + 3*b / 2 - bw / 2, offset), bw, h - hf, linewidth=1, edgecolor=color,
                                 facecolor='none',
                                 hatch=hatch, fill=False)

    # Add the rectangle to the plot
    ax.add_patch(rect_flange)
    ax.add_patch(rect_rib1)
    ax.add_patch(rect_rib2)

    # # Add dimension annotations
    # ax.annotate(f'b = {width:.2f} m', xy=(offset + width / 2, 0.05), xytext=(offset + width / 2, 0.06), ha='center')
    # ax.annotate(f'h = {height:.2f} m', xy=(0.02, offset + height / 2), xytext=(0.01, offset + height / 2),
    #             va='center', rotation='vertical')

    # Draw arrows for dimensions
    # ax.annotate('', xy=(0.1, 0.05), xytext=(0.1 + width, 0.05), arrowprops=dict(arrowstyle='|-|', color='black'))
    # ax.annotate('', xy=(0.05, 0.1), xytext=(0.05, 0.1 + height), arrowprops=dict(arrowstyle='|-|', color='black'))

    # Hide the x and y axes
    ax.axis('off')

    # Set the aspect of the plot to be equal
    ax.set_aspect('equal')

    # Set the limits of the plot
    ax.set_xlim(0, b + 10 * offset)
    ax.set_ylim(0, h + 4 * offset)

    return fig, ax, offset

def plot_wd_rib_with_dimensions(bw, h, b, t2, t3, color='black', hatch='--', offset=0.1):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Define the rectangle with hatching (lower-left corner at (x, y), width, and height)
    rect_flange2 = patches.Rectangle((offset, offset), 2*b, t2, linewidth=1, edgecolor=color, facecolor='none',
                             hatch='--', fill=False)
    rect_flange3 = patches.Rectangle((offset, offset + t2+h), 2*b, t3, linewidth=1, edgecolor=color, facecolor='none',
                                     hatch='--', fill=False)
    rect_rib1 = patches.Rectangle((offset+a/2, offset+t2), bw, h, linewidth=1, edgecolor=color, facecolor='none',
                             hatch='-', fill=False)
    rect_rib2 = patches.Rectangle((offset+3*a/2, offset+t2), bw, h, linewidth=1, edgecolor=color, facecolor='none',
                             hatch='-', fill=False)


    # Add the rectangle to the plot
    ax.add_patch(rect_flange2)
    ax.add_patch(rect_flange3)
    ax.add_patch(rect_rib1)
    ax.add_patch(rect_rib2)

    # Add dimension annotations
    ax.annotate(f'bw_Rippe = {bw:.2f} m', xy=(offset + bw, 0.05), xytext=(offset + bw / 2, 0.06), ha='center')
    ax.annotate(f'bw = {bw:.2f} m', xy=(offset + bw/2, 0.05), xytext=(offset + 3*bw / 2, -0.16), ha='center')
    ax.annotate(f'h = {h:.2f} m', xy=(0.02, offset + h / 2), xytext=(0.01, offset + h / 2),
                va='center', rotation='vertical')

    # #Draw arrows for dimensions
    # ax.annotate('', xy=(0.1, 0.05), xytext=(0.1 + width, 0.05), arrowprops=dict(arrowstyle='|-|', color='black'))
    # ax.annotate('', xy=(0.05, 0.1), xytext=(0.05, 0.1 + height), arrowprops=dict(arrowstyle='|-|', color='black'))

    # Hide the x and y axes
    ax.axis('off')

    # Set the aspect of the plot to be equal
    ax.set_aspect('equal')

    # Set the limits of the plot
    ax.set_xlim(0, 2*b + 2 * offset)
    ax.set_ylim(0, h+t2+t3 + 4 * offset)

    return fig, ax, offset

def plot_rebars_long(ax, section, offset, color='blue'):
    # get rebar positions
    rebar_positions = get_rebar_positions(section)
    # plot rebars
    for (x, y, di) in rebar_positions:
        rebar = plt.Circle((x+offset, y+offset), di/2, color=color)
        ax.add_patch(rebar)

def plot_stirrups(ax, section, offset, color='blue'):
    # get stirrup positions
    stirrup_positions = get_stirrup_positions(section)
    # plot stirrups
    for (x1, y1, x2, y2) in stirrup_positions:
        stirrup = plt.Line2D([x1+offset, x2+offset], [y1+offset, y2+offset], color=color, linewidth=2)
        ax.add_line(stirrup)

def get_rebar_positions(section):
    # create x and y coordinates of lower longitudinal reinforcement
    y_u = section.h - section.d
    s_xu = section.bw[0][1]
    x_u = [section.b/2]
    while max(x_u) + s_xu < section.b:
        x_u.append(max(x_u) + s_xu)
        x_u.append(min(x_u) - s_xu)

    # create x and y coordinates of upper longitudinal reinforcement
    y_o = section.ds
    s_xo = section.bw[1][1]
    x_o = [section.b/2]
    while max(x_o) + s_xo < section.b:
        x_o.append(max(x_o) + s_xo)
        x_o.append(min(x_o) - s_xo)

    # assemble rebar positions and dimensions relative to cross-section left lower edge
    di_xu = section.bw[0][0]
    di_xo = section.bw[1][0]
    rebar_positions = []
    for xi in x_u:
        rebar_i = (xi, y_u, di_xu)
        rebar_positions.append(rebar_i)
    for xi in x_o:
        rebar_i = (xi, y_o, di_xo)
        rebar_positions.append(rebar_i)
    return rebar_positions


def get_stirrup_positions(section):
    # create coordinates of stirrup edge points
    n_stirrup = section.bw_bg[2]
    di_stirrup = section.bw_bg[0]
    edge_dist = section.c_nom + di_stirrup/2
    # create x-coordinates of vertical stirrups
    x_linspace = np.linspace(edge_dist, section.b-edge_dist, n_stirrup)
    # create y-coordinates of stirrups-endings
    y_u = edge_dist
    y_o = section.h - edge_dist
    # create lines between edge points
    stirrup_positions = []
    for idx, xi in enumerate(x_linspace):
        # create vertical lines
        line_vert = (xi, y_u, xi, y_o)
        stirrup_positions.append(line_vert)
        if idx < x_linspace.size-1:
            # create horizontal lines
            line_u = (xi, y_u, x_linspace[idx+1], y_u)
            stirrup_positions.append(line_u)
            line_o = (xi, y_o, x_linspace[idx+1], y_o)
            stirrup_positions.append(line_o)
    return stirrup_positions


# PLOT DATASETS OF CROSS_SECTION WITH VARIED MATERIALS IN M-CHI PLOT AND PLOT THE OPTIMIZED SECTIONS FOR VALIDATION
# ----------------------------------------------------------------------------------------------------------------------
def plot_section_dataset(database_name, crsec_type, mat_names, ax, gwp_budget=50, basetype="epd"):
    # GENERATE INITIAL CROSS-SECTIONS
    # Search database (table products, attribute material) for products,
    # get prod_id of relevant materials from database and create initial cross-section for each product
    to_plot = []
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    mat_nr = -1
    x_values = []
    y_values = []
    for mat_name in mat_names:
        inquiry = ("SELECT PRO_ID FROM products WHERE"
                   " MATERIAL=" + mat_name + source_filter(basetype))
        cursor.execute(inquiry)
        result = cursor.fetchall()
        for i, prod_id in enumerate(result):
            mat_nr += 1  # number for annotation in plot
            # create materials for wooden cross-sections, derive corresponding design values
            prod_id_str = "'" + str(prod_id[0]) + "'"
            inquiry = ("SELECT MECH_PROP FROM products WHERE"
                       " PRO_ID=" + prod_id_str)
            cursor.execute(inquiry)
            result = cursor.fetchall()
            mech_prop = "'" + result[0][0] + "'"
            if crsec_type == "wd_rec":
                # create a Wood material object
                timber = struct_analysis.Wood(mech_prop, database_name, prod_id_str)
                timber.get_design_values()
                # create initial wooden rectangular cross-section
                section_0 = struct_analysis.RectangularWood(timber, 1.0, 0.12)
                color = "tab:brown"
            elif crsec_type == "rc_rec":
                # create a Concrete material object
                concrete = struct_analysis.ReadyMixedConcrete(mech_prop, database_name, prod_id=prod_id_str)
                concrete.get_design_values()
                # create a Rebar material object
                rebar = struct_analysis.SteelReinforcingBar("'B500B'", database_name)
                # create initial wooden rectangular cross-section
                section_0 = struct_analysis.RectangularConcrete(concrete, rebar, 1.0, 0.12,
                                                                0.014, 0.15, 0.01, 0.15,
                                                                0, 0.15, 2)
                color = "tab:green"
            elif crsec_type == "rc_rib":
                # create a Concrete material object
                concrete = struct_analysis.ReadyMixedConcrete(mech_prop, database_name, prod_id=prod_id_str)
                concrete.get_design_values()
                # create a Rebar material object
                rebar = struct_analysis.SteelReinforcingBar("'B500B'", database_name)
                # create initial wooden rectangular cross-section
                section_0 = struct_analysis.RibbedConcrete(concrete, rebar, 4, 1.5, 0.14, 0.3, 0.18, 0.008, 0.15, 0.008, 0.15, 0.02, 5, 0.008, 0.15, 2)
                color = 'mediumseagreen'
## XXXXXXXXXXX neuen Querschnittstyp initialisieren
            else:
                print("cross-section type is not defined inside function plot_dataset()")
                section_0 = []
                color = "tab:grey"


            #
            # maximizing Mu by varying the geometry within the max allowed gwp-budget.
            opt_section = struct_optimization.get_opt_sec(section_0, gwp_budget)

            # add M-Chi relationship to plot
            x_values, y_values = plot_m_chi(opt_section, ax, mat_nr, x_values, y_values)

            # plot cross-section
            plot_section(opt_section)
            plt.title(f'#{mat_nr}')

    # ## Add envelope of dataset to plot
    # # Combine x and y into a single array for ConvexHull
    # x = [item for sublist in x_values for item in sublist]
    # y = [item for sublist in y_values for item in sublist]
    # points = np.column_stack((x, y))
    # # points = [item for sublist in points_nested for item in sublist]
    # print(points.shape)
    # hull = ConvexHull(points)
    #
    # # Plot the envelope area (convex hull)
    # for simplex in hull.simplices:
    #     ax.plot(points[simplex, 0], points[simplex, 1], 'r-')
#
#     # Fill the hull area
#     hull_vertices = points[hull.vertices]
#     ax.fill(hull_vertices[:, 0], hull_vertices[:, 1], color, alpha=0.3, label="Envelope")

    ## Add envelope of dataset to plot
    # Define a common x-axis for interpolation
    common_x = sorted(set(np.concatenate(x_values)))
    # Interpolate y-values onto the common x-axis
    interpolated_y_values_min = []
    interpolated_y_values_max = []
    # y_test = []
    for x, y in zip(x_values, y_values):
        # define interpolation functions with different rules, when x is out of range
        f1 = interp1d(x, y, kind='linear', bounds_error=False, fill_value="extrapolate")
        f2 = interp1d(x, y, kind='linear', bounds_error=False, fill_value=(0, 0))
        a = []
        b = []
        for xi in common_x:
            if xi >= 0:  # apply interpolation functions withe rules for positive x_values
                a.append(float(f1(xi)))
                b.append(float(f2(xi)))
            else:  # apply interpolation functions withe rules for negative x_values
                b.append(float(f1(xi)))
                a.append(float(f2(xi)))
        interpolated_y_values_min.append(a)
        interpolated_y_values_max.append(b)

    y_lower = np.min(interpolated_y_values_min, axis=0)
    y_upper = np.max(interpolated_y_values_max, axis=0)

    # Fill the area between the envelope
    ax.fill_between(common_x, y_lower, y_upper, color=color, alpha=0.3, label='Envelope')



# plot m-chi relationship for a defined cross-section
def plot_m_chi(section, ax, i, x_values, y_values):
    # add M-Chi relationship to plot
    if section.section_type[0:2] == "wd":
        color = "tab:brown"  # color for wood
        chi_u_p, chi_u_n = section.mu_max/section.ei1, section.mu_min/section.ei1
        x = [chi_u_n, 0, chi_u_p]
        y = [section.mu_min, 0, section.mu_max]
    elif section.section_type[0:2] == "rc":
        color = "tab:green"  # color for reinforced concrete
        chi_r1_p, chi_r1_n = section.mr_p / section.ei1, section.mr_n / section.ei1
        chi_r2_p, chi_r2_n = section.mr_p / section.ei2, section.mr_n / section.ei2
        chi_y_p, chi_y_n = section.mu_max / section.ei2, section.mu_min / section.ei2
        chi_u_p, chi_u_n = section.concrete_type.ec2d/section.x_p, -section.concrete_type.ec2d/section.x_n
        if section.mr_p <= section.mu_max and section.mr_n >= section.mu_min:  # ductile behavior in both directions
            x = [chi_u_n, chi_y_n, chi_r2_n, chi_r1_n, 0, chi_r1_p, chi_r2_p, chi_y_p, chi_u_p]
            y = [section.mu_min, section.mu_min, section.mr_n, section.mr_n, 0, section.mr_p, section.mr_p,
                 section.mu_max, section.mu_max]
        elif section.mr_p <= section.mu_max and section.mr_n < section.mu_min:  # ductile behavior only for pos. moments
            x = [chi_r1_n, chi_r1_n, 0, chi_r1_p, chi_r2_p, chi_y_p, chi_u_p]
            y = [0, section.mr_n, 0, section.mr_p, section.mr_p,
                 section.mu_max, section.mu_max]
        elif section.mr_p > section.mu_max and section.mr_n >= section.mu_min:  # ductile behavior only for neg. moments
            x = [chi_u_n, chi_y_n, chi_r2_n, chi_r1_n, 0, chi_r1_p, chi_r1_p]
            y = [section.mu_min, section.mu_min, section.mr_n, section.mr_n, 0, section.mr_p, 0]
        else:  # no ductile behavior
            x = [chi_r1_n, chi_r1_n, 0, chi_r1_p, chi_r1_p]
            y = [0, section.mr_n, 0, section.mr_p, 0]
    else:
        print("M-Chi plot is not defined for sections of type " + section.section_type)
        x, y = 0, 0
        color = "tab:black"
    y_mod = [yi/1e3 for yi in y]  # modify unit of moment from Nm/m to kNm/m
    ax.plot(x, y_mod, color=color)  # plot m-Chi relationship with unit of moment: kNm/m
    ax.annotate(f'#{i}', xy=(x[-1], y_mod[-1]), xytext=(x[-1]*1.1, y_mod[-1]),
                 arrowprops=dict(facecolor='black', shrink=0.2, width=0.2, headwidth=2, headlength=4),
                 fontsize=9, color='black', va='center')
    x_values.append(x)
    y_values.append(y_mod)
    return x_values, y_values
    ## Define and plot envelope


# plt.annotate(f'#{i}', xy=(ver_x, ver_y),
#                          xytext=(ver_x + 0.05*lengths[-1], ver_y),
#                          arrowprops=dict(facecolor='black', shrink=0.2, width=0.2, headwidth=2, headlength=4),
#                          fontsize=9, color='black', va='center')