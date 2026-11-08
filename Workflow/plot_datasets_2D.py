import struct_analysis  # file with code for structural analysis
import struct_optimization  # verifications of the optimized members
import struct_optimization_2D  # file with code for structural optimization
import opt_and_plot  # shared product selection and mean materials
import sqlite3  # import modul for SQLite
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon
from scipy.interpolate import interp1d
import class_to_excel_2
from scipy.spatial import ConvexHull

# source filter (same conditions as in opt_and_plot.py)
# KBOB rows: only they have a "KBOB ID-Nr." (empty for EPD rows, NULL in the DB); every other row counts as EPD
KBOB_CONDITION = "(\"KBOB ID-Nr.\" IS NOT NULL)"


def source_filter(basetype):
    # SQL fragment selecting the data basis: product EPDs or generic KBOB values
    if basetype == "kbob":
        return f" AND {KBOB_CONDITION} AND Man_Ausschluss = 1 AND CAST(Total_GWP AS REAL) > 0 "
    elif basetype == "epd":
        return f" AND NOT {KBOB_CONDITION} AND ValidEPD = 1 AND Man_Ausschluss = 1 "
    raise ValueError(f"basetype must be 'epd' or 'kbob', got {basetype}")


# PLOT DATASETS OF MEMBERS WITH DEFINED CROSS_SECTIONS AND VARIED MATERIALS
# ----------------------------------------------------------------------------------------------------------------------
def plot_dataset(length_x,length_y, support, database_name, criteria, optima, floorstruc, requirements, crsec_type, mat_names,
                 g2k=0.75, qk=2.0, max_iter=100, idx_vrfctn=-1, basetype="epd", alg="basinhoppin", results=None,
                 file_tag="", mean_gwp=False, min_max_only=True, members_excel=True):
    # alg: "basinhoppin" or "TPE" (see struct_optimization_2D)
    # results: optional list; one dict per optimized member (incl. infeasible spans with member=None) is appended
    # file_tag: optional suffix of the Excel file name (avoids overwriting when runs share the same name)
    # mean_gwp: True -> additional "mean sections" (variant "mean", EPD only), see opt_and_plot.get_mean_materials
    # min_max_only: True -> per strength class only "minmin" (lowest GWP concrete + lowest GWP rebar) and "maxmax"
    #               (highest + highest); False -> every concrete x every rebar; same selection as 1D,
    #               see opt_and_plot.VARIANTS
    # members_excel: False -> no Members_2D_*.xlsx (the template writes its own result file)

    if idx_vrfctn == -1:
        idx_vrfctn = random.randint(0, len(length_x)-1)

    # GENERATE INITIAL CROSS-SECTIONS
    # Search database (table products, attribute material) for products
    # get prod_id of relevant materials from database and create initial cross-section for each product
    to_plot = []
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    # product selection as in 1D (opt_and_plot.get_main_selection): (prod_id string, mean material or None, variant)
    # To see the old version, run git show a3fc314:Workflow/plot_datasets_2D.py (around lines 49-68).
    for mat_name in mat_names:
        products = opt_and_plot.get_main_selection(cursor, mat_name.strip("'"), basetype, min_max_only,
                                                   mean_gwp and basetype == "epd")
        for prod_id_str, mean, variant in products:
            is_mean = mean is not None
            inquiry = ("""
                                SELECT MECH_PROP FROM products
                                WHERE  PRO_ID LIKE """ + prod_id_str
                       )
            # inquiry = ("SELECT mech_prop FROM products WHERE"
            #            " PRO_ID=" + prod_id_str)
            cursor.execute(inquiry)
            result = cursor.fetchall()
            mech_prop = f"'{opt_and_plot.strip_and_complete_mech_prop(result[0][0])}'"

            if crsec_type == "wd_rec":
                # create a Wood material object
                timber = struct_analysis.Wood(mech_prop, database_name, prod_id_str)
                timber.get_design_values()
                # create initial wooden rectangular cross-section
                section_0 = struct_analysis.RectangularWood(timber, 1.0, 0.1, xi=0.02)
                # add section to content-definition of plot-line
                line_i = [section_0, floorstruc, is_mean, variant]
                to_plot.append(line_i)

            elif crsec_type == "rc_rec":
                # create a Concrete material object
                concrete = struct_analysis.ReadyMixedConcrete(mech_prop, database_name, prod_id=prod_id_str)
                concrete.get_design_values()
                opt_and_plot.apply_mean_material(concrete, mean)
                # rebar of the same variant: minmin -> lowest GWP, maxmax -> highest GWP, all -> every rebar,
                # mean -> the mean rebar, kbob -> lowest and highest GWP (see opt_and_plot.get_secondary_selection)
                # To see the old version, run git show 36ba32b:Workflow/plot_datasets_2D.py (around lines 72–122).
                for rebar_prod_id, rebar_mean in opt_and_plot.get_secondary_selection(
                        cursor, 'Steel_reinforcing_bar', 'B500B', basetype, variant):
                    # create a rebar material object with mech prop B500B and low rsp high emission values
                    rebar = struct_analysis.SteelReinforcingBar("'B500B'", database_name, prod_id=rebar_prod_id)
                    opt_and_plot.apply_mean_material(rebar, rebar_mean)
                    # create initial cross-section
                    section_0 = struct_analysis.FlatSlab2D(concrete, rebar, 1.0, 0.20,
                                                           0.014, 0.15, 0.008, 0.15, 0.008, 0.15, 0.008, 0.15,
                                                           0, 0.15, 0,2.0,0.02,0.0, 0.15)
                    # add section to content-definition of plot-line
                    to_plot.append([section_0, floorstruc, is_mean, variant])

            elif crsec_type == "rc_rib":
                # create a Concrete material object
                concrete = struct_analysis.ReadyMixedConcrete(mech_prop, database_name, prod_id=prod_id_str)
                concrete.get_design_values()
                # search database for rebar material of type B500B with lowest and highes emissions
                inquiry = f"""
                                SELECT PRO_ID, MECH_PROP, Total_GWP FROM products
                                WHERE "MATERIAL" = 'Steel_reinforcing_bar'
                                  AND DENSITY IS NOT NULL
                                  AND MECH_PROP = 'B500B'
                                  {source_filter(basetype)}
                                  AND CAST(Total_GWP AS REAL) IN (
                                      SELECT MIN(CAST(Total_GWP AS REAL)) FROM products 
                                      WHERE "MATERIAL" = 'Steel_reinforcing_bar' 
                                        AND DENSITY IS NOT NULL 
                                        AND MECH_PROP = 'B500B' 
                                        {source_filter(basetype)}

                                      UNION

                                      SELECT MAX(CAST(Total_GWP AS REAL)) FROM products 
                                      WHERE "MATERIAL" = 'Steel_reinforcing_bar' 
                                        AND DENSITY IS NOT NULL 
                                        AND MECH_PROP = 'B500B' 
                                        {source_filter(basetype)}
                                  )
                                """
                cursor.execute(inquiry)
                result = cursor.fetchall()
                prod_id_low = result[0]
                prod_id_low_str = "'" + str(prod_id_low[0]) + "'"
                # result[-1] instead of result[1], KBOB has only one B500B rebar (low = high)
                prod_id_high = result[-1]
                prod_id_high_str = "'" + str(prod_id_high[0]) + "'"

                # create a rebar material objects with mech prop B500B and low rsp high emission values
                rebar_low_em = struct_analysis.SteelReinforcingBar("'B500B'", database_name, prod_id=prod_id_low_str)
                rebar_high_em = struct_analysis.SteelReinforcingBar("'B500B'", database_name, prod_id=prod_id_high_str)
                # TODO eventuell sind 3 d 16 eine bessere Startbewehrung im Sten (di_x_w und n_x_w), weil nur der Durchmesser, nicht aber die Anzahl Stäbe optimiert wird, oder wir nehmen noch die anzahl Stäbe in die Optimierung rein.
                # create initial cross-sections
                section_00 = struct_analysis.RibbedConcrete(concrete, rebar_low_em, 4, 1.0, 0.15, 0.3, 0.18, 0.01, 0.15,
                                                            0.01, 0.15, 0.018, 2, 0.01, 0.15, 2)
                section_01 = struct_analysis.RibbedConcrete(concrete, rebar_high_em, 4, 1.0, 0.15, 0.3, 0.18, 0.01,
                                                            0.15,
                                                            0.01, 0.15, 0.018, 3, 0.01, 0.15, 2)
                # add sections to content-definition of plot-line
                line_i0 = [section_00, floorstruc, is_mean, variant]
                line_i1 = [section_01, floorstruc, is_mean, variant]
                to_plot.extend([line_i0, line_i1])



    # ANALYSIS AND OPTIMIZATION OF CROSS-SECTIONS
    member_list = []
    legend = []
    sup=support[0]
    # create plot data
    for i in to_plot:
        for criterion in criteria:
            for optimum in optima:
                members = []
                for j, (lx, ly) in enumerate(zip(length_x, length_y)):
                    sys = struct_analysis.Slab(lx, ly, sup)
                    member0 = struct_analysis.Member2D(i[0], sys, i[1], requirements, g2k, qk)
                    opt_section = struct_optimization_2D.get_optimized_section(member0, criterion, optimum, max_iter,
                                                                               alg=alg)
                    # Handle infeasible solutions: stays None so that members[j] still belongs to span j
                    if opt_section is None:
                        print(f"Warning: no feasible {crsec_type} section for span {lx} x {ly} m -> no section in output")
                        opt_member = None
                        failed = ["no section"]
                    else:
                        opt_member = struct_analysis.Member2D(opt_section, sys, i[1], requirements, g2k, qk)
                        failed = struct_optimization.failed_checks(opt_member)
                    # section that fails a verification: only in results (feasible = False), not in plots / Members_*.xlsx
                    members.append(None if failed else opt_member)
                    if results is not None:
                        results.append({"member": opt_member, "section_0": i[0], "length": lx, "criterion": criterion,
                                        "optimum": optimum, "dataset": len(member_list), "mean_section": i[2],
                                        "variant": i[3], "failed_checks": failed})
                member_list.append(members)
                if i[0].section_type[0:2] == "rc":
                    material_lg = i[0].concrete_type.mech_prop + " + " + i[0].rebar_type.mech_prop
                elif i[0].section_type == "wd":
                    material_lg = i[0].wood_type.mech_prop
                elif i[0].section_type == "wd_rib":
                    material_lg = i[0].wood_type_1.mech_prop
                else:
                    material_lg = "error: section material is not defined"
                legend.append([i[0].section_type, material_lg, criterion, optimum])

    # CREATE DATA OF ENVELOPE AREA OF DATASET
    # Envelopes per span over the feasible members only; spans without any feasible member are left out (as in 1D)
    # subplot 1: structural height, subplot 2: total height, subplot 3: co2 of structure, subplot 4: total co2
    members_per_length = [[mem for mem in col if mem is not None] for col in zip(*member_list)]
    idx_feasible = [j for j, mems in enumerate(members_per_length) if mems]
    lengths_filtered = [length_x[j] for j in idx_feasible]
    value_getters = [lambda mem: mem.section.h,
                     lambda mem: mem.section.h + mem.floorstruc.h_Floor,
                     lambda mem: mem.section.co2,
                     lambda mem: mem.section.co2 + mem.floorstruc.co2_Floor]
    values_min, values_max = [], []
    for get_value in value_getters:
        per_length = [[get_value(mem) for mem in members_per_length[j]] for j in idx_feasible]
        values_min.append([min(values) for values in per_length])
        values_max.append([max(values) for values in per_length])

    # PLOT DATASET TO FIGURE
    plt.figure(1)
    data_max = [0, 0, 0, 0]
    vrfctn_members = [[], []]
    for i, members in enumerate(member_list):
        plotdata = [[], [], [], []]
        x_data = []  # spans of this dataset with a feasible member
        for j, mem in enumerate(members):
            if mem is None:  # no feasible section for span j
                continue
            x_data.append(length_x[j])
            plotdata[0].append(mem.section.h)
            plotdata[1].append(mem.section.h + mem.floorstruc.h_Floor)
            plotdata[2].append(mem.section.co2)
            plotdata[3].append(mem.section.co2 + mem.floorstruc.co2_Floor)
            if j == idx_vrfctn:
                vrfctn_members[0].append(mem)
                vrfctn_members[1].append(i)
        sec_typ, mat, cri, opt = legend[i]
        # set line color
        if sec_typ == "rc_rec" and sup=="LL-frei":
            color = 'green'  # color for reinforced concrete
        elif sec_typ == "rc_rec" and sup == "LL-eingespannt":
            color = 'red'  # color for reinforced concrete
        elif sec_typ == "rc_rec":
            color = 'lightgreen'  # color for reinforced concrete
        elif sec_typ == "wd_rec":
            color = 'saddlebrown'  # color for wood
        elif sec_typ == "rc_rib":
            color = 'limegreen'  # color for reinforced concrete
        elif sec_typ == "wd_rib":
            color = 'sandybrown'  # color for wood

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
        label = sec_typ + ", " + mat + ", " + cri + ", optimized for " + opt
        # plot data
        for idx, data in enumerate(plotdata):
            plt.subplot(2, 2, idx + 1)
            # plot area (needs at least 2 feasible spans)
            if len(lengths_filtered) >= 2:
                # prepare area
                coords = (list(zip(lengths_filtered, values_max[idx]))
                          + list(zip(lengths_filtered[::-1], values_min[idx][::-1])))
                # create a polygon from the coordinates
                polygon = Polygon(coords)
                # extract the x and y coordinates for plotting
                x, y = polygon.exterior.xy
                plt.fill(x, y, alpha=0.05, facecolor=color)
            # plot lines
            plt.plot(x_data, data, color=color, linestyle=linestyle, linewidth=linewidth, label=label, alpha=0.2)
            data_max[idx] = max([data_max[idx]] + data)
            # # plot points of verification into graph
            # ver_x, ver_y = lengths[idx_vrfctn], data[idx_vrfctn]
            # plt.plot(ver_x, ver_y, 'o', color='black', markersize=2)
            # plt.annotate(f'#{i}', xy=(ver_x, ver_y),
            #              xytext=(ver_x + 0.05*lengths[-1], ver_y),
            #              arrowprops=dict(facecolor='black', shrink=0.2, width=0.2, headwidth=2, headlength=4),
            #              fontsize=9, color='black', va='center')

     # create Excel sheets
    members_2d = [
            member
            for pair in member_list
            for member in pair
            if member is not None
    ]
    if not members_excel:
        pass
    elif crsec_type == "rc_rec" and sup == "LL-eingespannt":
        class_to_excel_2.members_to_excel2(members_2d, f"Members_2D_LL_eingespannt_{basetype}{file_tag}.xlsx", folder="Results")
    elif crsec_type == "rc_rec" and sup == "LL-frei":
        class_to_excel_2.members_to_excel2(members_2d, f"Members_2D_LL_frei_{basetype}{file_tag}.xlsx", folder="Results")
    elif crsec_type == "rc_rec" and sup == "PL-eingespannt":
        class_to_excel_2.members_to_excel2(members_2d, f"Members_2D_PL_eingespannt_{basetype}{file_tag}.xlsx", folder="Results")
    else:
        print("cross-section type is not defined inside function plot_dataset() for Excel-generation")

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
                  f'GWP = {section.co2:.0f} kg/m^2')
    elif section.section_type == "wd_rec":  # Rectangular Wooden Cross-Section
        fig, ax, offset = plot_rectangle_with_dimensions(section.b, section.h, 'brown', '/')
        legend = (f'{section.wood_type.mech_prop}, prod_ID:{section.wood_type.prod_id} \n'
                  f'GWP = {section.co2:.0f} kg/m^2')

    elif section.section_type == "rc_rib": #Betonrippenquerschnitte
        fig, ax, offset = plot_rib_with_dimensions(section.b, section.b_w, section.h, section.h_f, 'green', 'x')
        legend = (f'{section.concrete_type.mech_prop}, prod_ID:{section.concrete_type.prod_id} \n'
              f'length = {section.l0} \n'
              f'{section.rebar_type.mech_prop}, prod_ID:{section.rebar_type.prod_id} \n'
              f'di_r = {section.bw_r[0]:.3f} \n'
              f'di_xu / s_xu = {section.bw[0][0]:.3f} / {section.bw[0][1]} \n'
              #f'di_stir / s_stir / n = {section.bw_bg[0]} / {section.bw_bg[1]} / {section.bw_bg[2]}\n'
              f'c_nom = {100 * section.c_nom:.1f} cm \n'
              f'x/d = {section.x_p / section.d:.2f} \n'
              f'h, hf, hw, b, bw = {section.h:.2f}, {section.h_f:.2f}, {section.h_w:.2f}, {section.b:.2f}, {section.b_w:.2f} \n'
              f'GWP = {section.co2:.0f} kg/m^2')

    elif section.section_type == "wd_rib": #Betonrippenquerschnitte
        fig, ax, offset = plot_wd_rib_with_dimensions(section.b, section.h, section.a, section.t2, section.t3, 'brown', 'x')
        legend = (f'{section.wood_type_1.mech_prop}, prod_ID:{section.wood_type_1.prod_id} \n'
              f'length = {section.l0} \n'
              f'h, b, a, t2, t3 = {section.h:.2f}, {section.b:.2f}, {section.a:.2f}, {section.t2:.2f}, {section.t3:.2f} \n'
              f'GWP = {section.co2:.0f} kg/m^2')

    else:
        print("no plot for specified section_type defined jet")
        fig, ax = plt.subplots()
        legend = f'no plot for section_type "{section.section_type}" defined jet'
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

def plot_wd_rib_with_dimensions(b, h, a, t2, t3, color='black', hatch='--', offset=0.1):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Define the rectangle with hatching (lower-left corner at (x, y), width, and height)
    rect_flange2 = patches.Rectangle((offset, offset), 2*a, t2, linewidth=1, edgecolor=color, facecolor='none',
                             hatch='--', fill=False)
    rect_flange3 = patches.Rectangle((offset, offset + t2+h), 2*a, t3, linewidth=1, edgecolor=color, facecolor='none',
                                     hatch='--', fill=False)
    rect_rib1 = patches.Rectangle((offset+a/2, offset+t2), b, h, linewidth=1, edgecolor=color, facecolor='none',
                             hatch='-', fill=False)
    rect_rib2 = patches.Rectangle((offset+3*a/2, offset+t2), b, h, linewidth=1, edgecolor=color, facecolor='none',
                             hatch='-', fill=False)


    # Add the rectangle to the plot
    ax.add_patch(rect_flange2)
    ax.add_patch(rect_flange3)
    ax.add_patch(rect_rib1)
    ax.add_patch(rect_rib2)

    # Add dimension annotations
    ax.annotate(f'b_Rippe = {b:.2f} m', xy=(offset + b, 0.05), xytext=(offset + b / 2, 0.06), ha='center')
    ax.annotate(f'b = {b:.2f} m', xy=(offset + b/2, 0.05), xytext=(offset + 3*b / 2, -0.16), ha='center')
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
    ax.set_xlim(0, 2*a + 2 * offset)
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
def plot_section_dataset(database_name, crsec_type, mat_names, ax, gwp_budget=50):
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
                   " MATERIAL=" + mat_name)
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
            mech_prop = f"'{opt_and_plot.strip_and_complete_mech_prop(result[0][0])}'"
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
                section_0 = struct_analysis.RibbedConcrete(concrete, rebar, 4, 1.0, 0.14, 0.3, 0.18, 0.01, 0.15, 0.01, 0.15, 0.02, 2, 0.01, 0.15, 2)
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