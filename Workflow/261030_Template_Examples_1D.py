# TEMPLATE for running examples (2D slabs: 261030_Template_Examples_2D.py): 1D members (simple beam / continuous / two span) in reinforced concrete and wood
# with different cross-sections and settings.
#
# HOW TO USE: copy this file and only adjust PART 1 (DEFAULTS and RUNS).
# Before the first optimization starts, all runs are checked (allowed values, allowed combinations, products in the
# database). If anything is wrong, the script stops with a list of all errors and nothing is optimized.
# The results are written into one Excel (Results/<timestamp>_Members_1D.xlsx): one sheet per run (00, 01, ...) with
# the best member per span and material variant (minmin / mean / maxmax, see min_max_only) and the sheet "runs".
# Optional (SAVE_BATCH): Results/<timestamp>_batch_1D.xlsx with every optimized member. Plotting is done separately.


# ======================================================================================================================
# PART 1: SETTINGS (adjust here)
# ======================================================================================================================

# True: only check the runs and print the overview table, no optimization
CHECK_ONLY = False
# True: additionally save the batch file (every optimized member of every run, incl. infeasible ones)
SAVE_BATCH = False

#-----------------------------------------------------------------------------------------------------------------------
# DEFAULTS: used for every key a run does not set itself
DEFAULTS = {
    "system": "Simple Beam",    # "Simple Beam", "Continuous 1D", "Two span 1D 1D"
    "basetype": "epd",          # data basis: "epd" (product EPDs) or "kbob" (generic KBOB v9.0 values)
    "alg": "TPE",               # rc sections: "basinhoppin" or "TPE" (wd_rec / wd_rib use their own algorithm)
    "max_iter": 50,             # max. number of iterations per optimization. Higher value leads to better results
    "lengths": [4, 6, 8, 10, 12],  # system lengths [m], at least 2 values
    "criteria": ["ENV"],        # "ULS", "SLS1" (deflections), "SLS2" (vibrations), "FIRE", "ENV" (all together)
    "optima": ["GWP"],          # "GWP" (min. GWP), "h" (min. height); several possible; wd_rec ignores this
    "g2k": 0.75e3,              # n.t. Einbauten [N/m2]
    "qk": 2e3,                  # Nutzlast [N/m2]
    "use": "Wohnen",            # building use (Nutzung), only a label in the results; qk must fit it
    "min_max_only": True,       # True: per strength class 2 sections: "minmin" (lowest GWP product with MIN_MAX = 1
                                # + lowest GWP rebar / board) and "maxmax" (highest + highest); a class with only
                                # 1 product has no minmin / maxmax (only mean). False: every product x every
                                # rebar / board (variant "all", much longer runtime).
                                # Members file: best member per span within each variant (all strength classes,
                                # materials and t3 cases compete); only for basetype "epd", ignored for "kbob"
    "mean_gwp": True,           # True: additional "mean sections" (variant "mean"): one per strength class of the
                                # materials of the run, with the density-weighted mean GWP and the mean density of all
                                # products of that class (GWP * density = mean CO2 per m3); rebar (B500B) and board
                                # (C24) are means as well; wd_rib: both t3 cases
                                # are kept; only for basetype "epd", ignored for "kbob"
}

#-----------------------------------------------------------------------------------------------------------------------
# RUNS: Set the parameters you want to use
# crsec_type | floor 
# "rc_rec"   | "massiv", "Schuettung"
# "rc_rib"   | "Schuettung", "massiv"
# "wd_rec"   | "Vollholz"
# "wd_rib"   | "Hohlkasten"
RUNS = [
    {"crsec_type": "rc_rec", "floor": "massiv", "max_iter": 10},
    {"crsec_type": "rc_rib", "floor": "Schuettung", "max_iter": 10},
    {"crsec_type": "wd_rec", "floor": "Vollholz", "max_iter": 10},
    {"crsec_type": "wd_rib", "floor": "Hohlkasten", "max_iter": 10},
    # {"crsec_type": "rc_rec", "floor": "massiv", "system": "Continuous 1D"},
    # {"crsec_type": "rc_rib", "floor": "Schuettung", "system": "Continuous 1D"},
]


# ======================================================================================================================
# PART 2: FIXED DEFINITIONS AND PROGRAM CODE
# Not meant to be changed for running optimizations. Change only to extend the template itself
# (e.g. a new floor structure, a new material or a new allowed combination).
# ======================================================================================================================

# IMPORT
import struct_analysis  # file with code for structural analysis
import opt_and_plot  # file with code for optimization and plotting results in a standardized way
import pandas as pd
import sqlite3
import os
import time
import traceback
import numbers
from datetime import datetime
from openpyxl.styles import PatternFill

database_name = "database_261009.db"
results_folder = "Results"

# define service limit state criteria
req = struct_analysis.Requirements()

#-----------------------------------------------------------------------------------------------------------------------
# FLOOR STRUCTURES (non load bearing layers: [product name, thickness or False for default, False])
# The name is used in the Excel file name and the result tables.
h_ins = 0.18
FLOORS = {
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

#-----------------------------------------------------------------------------------------------------------------------
# MATERIALS (table products, attribute material); chosen by the prefix of crsec_type
MATERIALS = {
    "rc": ["'ready_mixed_concrete'"],
    "wd": ["'Glue_laminated_timber'", "'Solid_structural_timber'"],
}

#-----------------------------------------------------------------------------------------------------------------------
# ALLOWED VALUES AND COMBINATIONS
SYSTEMS = ["Simple Beam", "Continuous 1D", "Two span 1D 1D"]
BASETYPES = ["epd", "kbob"]
ALGS = ["TPE", "basinhoppin"]
CRITERIA = ["ULS", "SLS1", "SLS2", "FIRE", "ENV"]
OPTIMA = ["GWP", "h"]
# floor structures that fit a cross-section type:
#   Hohlkasten only with wd_rib (insulation lies within the box -> h_Floor is reduced by h_ins)
#   wd_rib only with Hohlkasten (REI60 requires the Steinwolle, see FLOORS)
ALLOWED_FLOORS = {
    "rc_rec": ["massiv", "Schuettung"],
    "rc_rib": ["Schuettung", "massiv"],
    "wd_rec": ["Vollholz"],
    "wd_rib": ["Hohlkasten"],
}
ALLOWED_KEYS = set(DEFAULTS) | {"crsec_type", "floor", "mat_names", "label"}


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) # returns true for int & float


def check_run(i, entry, run):
    # returns a list of error messages for one run (empty list: run is valid)
    err = []
    unknown = set(entry) - ALLOWED_KEYS
    if unknown:
        err.append(f"unknown key(s) {sorted(unknown)}; allowed: {sorted(ALLOWED_KEYS)}")
    crsec, floor = run.get("crsec_type"), run.get("floor")
    if crsec not in ALLOWED_FLOORS:
        err.append(f"crsec_type must be one of {list(ALLOWED_FLOORS)}, got {crsec!r}")
    if floor not in FLOORS:
        err.append(f"floor must be one of {list(FLOORS)}, got {floor!r}")
    elif crsec in ALLOWED_FLOORS and floor not in ALLOWED_FLOORS[crsec]:
        err.append(f"floor {floor!r} does not fit {crsec}; allowed: {ALLOWED_FLOORS[crsec]}")
    if run["system"] not in SYSTEMS:
        err.append(f"system must be one of {SYSTEMS}, got {run['system']!r}")
    if run["basetype"] not in BASETYPES:
        err.append(f"basetype must be one of {BASETYPES}, got {run['basetype']!r}")
    if run["alg"] not in ALGS:
        err.append(f"alg must be one of {ALGS}, got {run['alg']!r}")
    if not (isinstance(run["max_iter"], int) and run["max_iter"] > 0):
        err.append(f"max_iter must be a positive integer, got {run['max_iter']!r}")
    lengths = run["lengths"]
    if not (isinstance(lengths, list) and len(lengths) >= 2 and all(is_number(l) and l > 0 for l in lengths)):
        err.append(f"lengths must be a list of at least 2 positive numbers, got {lengths!r}")
    elif lengths != sorted(set(lengths)):
        err.append(f"lengths must be ascending without duplicates, got {lengths}")
    for key, allowed in (("criteria", CRITERIA), ("optima", OPTIMA)):
        values = run[key]
        if not (isinstance(values, list) and values and set(values) <= set(allowed) and len(set(values)) == len(values)):
            err.append(f"{key} must be a non-empty list of different values from {allowed}, got {values!r}")
    if not isinstance(run["min_max_only"], bool):
        err.append(f"min_max_only must be True or False, got {run['min_max_only']!r}")
    if not isinstance(run["mean_gwp"], bool):
        err.append(f"mean_gwp must be True or False, got {run['mean_gwp']!r}")
    if not (isinstance(run["use"], str) and run["use"]):
        err.append(f"use must be a non-empty text, got {run['use']!r}")
    for key in ("g2k", "qk"):
        if not (is_number(run[key]) and run[key] >= 0):
            err.append(f"{key} must be a number >= 0, got {run[key]!r}")
    # combinations of cross-section type and settings that give no meaningful result
    if crsec == "wd_rib" and "FIRE" in run["criteria"]:
        err.append("wd_rib: fire is not checked, criterion 'FIRE' gives no result")
    if crsec == "wd_rec" and len(run["optima"]) > 1:
        err.append("wd_rec ignores optima (always smallest feasible h) -> use only one entry, otherwise datasets repeat")
    if "mat_names" in entry and not (isinstance(entry["mat_names"], list) and entry["mat_names"]):
        err.append(f"mat_names must be a non-empty list, got {entry['mat_names']!r}")
    return err


def check_database(batch):
    # adds error messages into the error vector if there are products the runs need but the database does not contain
    err = []
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    checked = set()
    for run in batch:
        base, crsec = run["basetype"], run["crsec_type"]
        # CHECK MAIN MATERIALS (same query as plot_dataset)
        min_max_only = run["min_max_only"] and base == "epd"
        for mat_name in run["mat_names"]:
            if (mat_name, base, min_max_only) in checked:
                continue
            checked.add((mat_name, base, min_max_only))
            cursor.execute("SELECT COUNT(*) FROM products WHERE DENSITY IS NOT NULL AND MECH_PROP IS NOT NULL"
                           " AND \"MATERIAL\" LIKE " + mat_name + opt_and_plot.source_filter(base)
                           + opt_and_plot.min_max_filter(min_max_only))
            if cursor.fetchone()[0] == 0:
                err.append(f"run {run['nr']}: no product for material {mat_name} with basetype {base!r}, "
                           f"min_max_only={min_max_only}")
        # CHECK SECONDARY MATERIALS: rebar for rc, boards for wd_rib (same queries as plot_dataset)
        extra = {"rc": ("Steel_reinforcing_bar", "B500B"),
                 "wd_rib": ("%3_and_5_plywood%", "C24" if base == "epd" else None)}
        mean_extra = {"rc": ("Steel_reinforcing_bar", "B500B"), "wd_rib": ("%3_and_5_plywood%", "C24")}
        key = crsec[:2] if crsec[:2] == "rc" else crsec
        use_mean = run["mean_gwp"] and base == "epd"
        if key in extra and (key, base, use_mean) not in checked:
            checked.add((key, base, use_mean))
            try:
                opt_and_plot.get_low_high_prod_ids(cursor, *extra[key], base)
                if use_mean:
                    opt_and_plot.get_mean_materials(cursor, *mean_extra[key], base)
            except ValueError as e:
                err.append(f"run {run['nr']}: {e}")
    connection.close()
    # floor structures: every used floor must be readable from the database
    for name in sorted({run["floor"] for run in batch}):
        try:
            get_floor(name)
        except Exception as e:
            err.append(f"floor {name!r} cannot be built from the database: {e!r}")
    return err


def effective_key(run):
    # fingerprint of all settings that change the result; equal keys = duplicate runs
    # ignored settings are set to None/False: alg for wd, optima for wd_rec, min_max_only and mean_gwp for kbob
    return (run["crsec_type"], run["system"], run["floor"], run["basetype"], run["max_iter"], tuple(run["lengths"]),
            tuple(run["criteria"]), tuple(run["mat_names"]), run["g2k"], run["qk"],
            run["min_max_only"] and run["basetype"] == "epd", run["mean_gwp"] and run["basetype"] == "epd",
            None if run["crsec_type"][:2] == "wd" else run["alg"],
            None if run["crsec_type"] == "wd_rec" else tuple(run["optima"]))


def prepare_runs(runs):
    # completes all runs with DEFAULTS and checks them; stops the script if any check fails
    if not runs:
        raise SystemExit("No runs defined -> activate at least one entry in RUNS.")
    batch, errors = [], []
    for i, entry in enumerate(runs):  # runs are counted from 0
        run = {**DEFAULTS, **entry}
        run_errors = check_run(i, entry, run)
        errors += [f"run {i}: {e}" for e in run_errors]
        if run_errors:
            continue
        run["nr"] = i
        run.setdefault("mat_names", MATERIALS[run["crsec_type"][:2]])
        # default label: main keys + every other setting that differs from DEFAULTS
        extra = [f"{k}={entry[k]}" for k in ("alg", "max_iter", "lengths", "criteria", "optima", "g2k", "qk", "use", "min_max_only",
                                  "mean_gwp")
                 if k in entry and entry[k] != DEFAULTS[k]]
        run.setdefault("label", ", ".join([run["crsec_type"], run["system"], run["floor"], run["basetype"]] + extra))
        batch.append(run)

    # Compare every run with every other run
    for a_idx, a in enumerate(batch):
        for b in batch[a_idx + 1:]:
            if effective_key(a) == effective_key(b):
                errors.append(f"runs {a['nr']} and {b['nr']} give the same result (identical effective settings)")
            if a["label"] == b["label"]:
                errors.append(f"runs {a['nr']} and {b['nr']} have the same label {a['label']!r}")

    #check database only if there are no errors yet in the error list
    if not errors: 
        errors += check_database(batch)
    
    # STOPS BEFORE STARTING THE RUNS IF THERE ARE ANY ERRORS
    if errors:
        print("\nINVALID RUNS - nothing was optimized:\n  " + "\n  ".join(errors))
        raise SystemExit(1)
    return batch


def runs_table(batch):
    cols = ["nr", "label", "crsec_type", "system", "floor", "basetype", "alg", "max_iter", "lengths", "criteria",
            "optima", "g2k", "qk", "use", "min_max_only", "mean_gwp", "mat_names"]
    return pd.DataFrame([{c: (str(r[c]) if isinstance(r[c], list) else r[c]) for c in cols} for r in batch])


#-----------------------------------------------------------------------------------------------------------------------
# FLOOR OBJECTS (each floor is read from the database once)
_floor_cache = {}


def get_floor(name):
    if name not in _floor_cache:
        floor = struct_analysis.FloorStruc(FLOORS[name], database_name, name=name)
        floor.h_Floor = floor.h_Floor - FLOOR_H_CORRECTION.get(name, 0)
        _floor_cache[name] = floor
    return _floor_cache[name]




#-----------------------------------------------------------------------------------------------------------------------
# RESULT TABLES: one Excel with one sheet per run
# Column blocks of a sheet: identification | settings | geometry | internal forces | materials | CO2 | loads
# A new cross-section type needs a function in SECTION_COLUMNS.

def material_columns(role, mat):
    return {role: getattr(mat, "mech_prop", None), f"{role}_prod_id": getattr(mat, "prod_id", None),
            f"{role}_GWP [kgCO2eq/kg]": getattr(mat, "GWP", None)}
   
   
           
# one function per section type: fills the 3 column blocks geometry, materials, co2
# if no valid section was found, only materials is filled
def rc_rec_columns(sec, feasible):
    mats = {**material_columns("concrete", sec.concrete_type), **material_columns("rebar", sec.rebar_type)}
    if not feasible:
        return {}, mats, {}
    geo = {"h_struct [m]": sec.h, "b [m]": sec.b, "rebar_content [kg/m3]": sec.Bew_Gehalt}
    co2 = {"co2_concrete [kgCO2eq/m2]": sec.co2_concrete / sec.b, "co2_rebar [kgCO2eq/m2]": sec.co2_rebar / sec.b,
           "co2_struct [kgCO2eq/m2]": sec.co2 / sec.b}
    return geo, mats, co2

def rc_rib_columns(sec, feasible):  # co2 of RibbedConcrete is already per m2
    mats = {**material_columns("concrete", sec.concrete_type), **material_columns("rebar", sec.rebar_type)}
    if not feasible:
        return {}, mats, {}
    geo = {"h_struct [m]": sec.h, "b [m]": sec.b, "b_w [m]": sec.b_w, "h_f [m]": sec.h_f,
           "rebar_content [kg/m3]": sec.Bew_Gehalt}
    co2 = {"co2_concrete [kgCO2eq/m2]": sec.co2_concrete, "co2_rebar [kgCO2eq/m2]": sec.co2_rebar,
           "co2_struct [kgCO2eq/m2]": sec.co2}
    return geo, mats, co2

def wd_rec_columns(sec, feasible):
    mats = material_columns("timber", sec.wood_type)
    if not feasible:
        return {}, mats, {}
    return {"h_struct [m]": sec.h, "b [m]": sec.b}, mats, {"co2_struct [kgCO2eq/m2]": sec.co2 / sec.b}

def wd_rib_columns(sec, feasible):  # h = rib height only; boards t2 (bottom) and t3 (top) are added
    mats = {**material_columns("timber", sec.wood_type_1), **material_columns("board", sec.wood_type_2)}
    if not feasible:
        return {}, mats, {}
    co2_rib = sec.bw * sec.h * sec.wood_type_1.GWP * sec.wood_type_1.density / sec.b
    geo = {"h_struct [m]": sec.h + sec.t2 + sec.t3, "b [m]": sec.b, "b_w [m]": sec.bw, "h_rib [m]": sec.h,
           "t2 [m]": sec.t2, "t3 [m]": sec.t3}
    co2 = {"co2_rib [kgCO2eq/m2]": co2_rib, "co2_board [kgCO2eq/m2]": sec.co2 - co2_rib,
           "co2_struct [kgCO2eq/m2]": sec.co2}
    return geo, mats, co2

SECTION_COLUMNS = {"rc_rec": rc_rec_columns, "rc_rib": rc_rib_columns,
                   "wd_rec": wd_rec_columns, "wd_rib": wd_rib_columns}



# colors of the columns in excel: green = configuration / selected data, yellow = results,
# red = key results (single columns, override the color of their block)
GREEN, YELLOW, RED = "C6EFCE", "FFEB9C", "FFC7CE"
BLOCK_COLORS = {"data source": GREEN, "design configuration": GREEN, "material selection": GREEN,
                "structural results": YELLOW, "co2 structure": YELLOW, "final indicators": YELLOW}
KEY_COLUMNS = ["MEd_n [kNm]", "MEd_p [kNm]", "VEd [kN]", "co2_struct [kgCO2eq/m2]"]
COLUMN_BLOCK = {}  # column name -> block, filled by member_row


def member_row(entry, run, k):
    # one row per member, built block by block (order of the blocks = order of the columns)
    mem = entry["member"]
    sec = mem.section if mem is not None else entry["section_0"]
    geo, mats, co2 = SECTION_COLUMNS[run["crsec_type"]](sec, mem is not None)
    rebar = {k: geo.pop(k) for k in ["rebar_content [kg/m3]"] if k in geo}  # belongs to the structural results
    blocks = {
        # member_id = <run in the batch>-<member in the run>, both counted from 0 (first member: 00-000)
        "identification": {"member_id": f"{run['nr']:02d}-{k:03d}", "criterion": entry["criterion"],
                           "optimum": entry["optimum"], "variant": entry["variant"]},
        "data source": {"basetype": run["basetype"], "use": run["use"]},
        "design configuration": {
            "plot_label": f"{run['system']}_{run['crsec_type']}_{run['floor']}_{run['basetype']}",
            "label": run["label"], "run_nr": run["nr"], "dataset": entry["dataset"],
            "crsec_type": run["crsec_type"], "system": run["system"],
            **({"alg": run["alg"]} if run["crsec_type"][:2] == "rc" else {}),
            "g2k [kN/m2]": run["g2k"] / 1e3, "qk [kN/m2]": run["qk"] / 1e3, "feasible": not entry["failed_checks"],
            "failed_checks": ", ".join(entry["failed_checks"])},
        "geometry": {"l_tot [m]": entry["length"], **geo},
        "material selection": {"mean_section": entry["mean_section"], **mats},
    }
    if mem is not None:
        fl = mem.floorstruc
        g_struct = sec.g0k / sec.b / 1e3
        blocks["structural results"] = {
            **rebar,
            "MEd_n [kNm]": mem.mEd_n / 1e3, "MEd_p [kNm]": mem.mEd_p / 1e3, "VEd [kN]": mem.vEd / 1e3}
        blocks["co2 structure"] = co2
        blocks["floor build-up"] = {
            "floor": run["floor"], "h_floor [m]": fl.h_Floor, "g_floor [kN/m2]": fl.gk_area / 1e3,
            "co2_floor [kgCO2eq/m2]": fl.co2_Floor, "co2_floor_per_year [kgCO2eq/m2a]": fl.co2_a_Floor}
        blocks["final indicators"] = {
            "h_tot [m]": geo["h_struct [m]"] + fl.h_Floor, "g_struct [kN/m2]": g_struct,
            "g_tot [kN/m2]": g_struct + fl.gk_area / 1e3,
            "co2_tot [kgCO2eq/m2]": co2["co2_struct [kgCO2eq/m2]"] + fl.co2_Floor}
    else:
        blocks["floor build-up"] = {"floor": run["floor"]}
    row = {}
    for block, cols in blocks.items():
        COLUMN_BLOCK.update(dict.fromkeys(cols, block))
        row.update(cols)
    return row


def write_sheet(writer, name, df):
    # writes one result sheet: colored headers per block, frozen header row and member_id, readable widths
    df.to_excel(writer, sheet_name=name, index=False)
    ws = writer.sheets[name]
    for cell in ws[1]:
        color = RED if cell.value in KEY_COLUMNS else BLOCK_COLORS.get(COLUMN_BLOCK.get(cell.value))
        if color:
            cell.fill = PatternFill("solid", fgColor=color)
        ws.column_dimensions[cell.column_letter].width = max(10, len(str(cell.value)) + 2)
    ws.freeze_panes = "B2"


def all_columns(sheet_rows):
    # column order of the longest row (feasible member), then the columns only other rows have (e.g. "note")
    columns = max((list(r) for r in sheet_rows), key=len)
    for r in sheet_rows:
        columns += [c for c in r if c not in columns]
    return columns


def write_excel(path, sheets, df_runs):
    # one sheet per run ({sheet name: rows}), last sheet "runs"; a run without rows (failed) has no sheet
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, sheet_rows in sheets.items():
            if sheet_rows:
                write_sheet(writer, name, pd.DataFrame(sheet_rows, columns=all_columns(sheet_rows)))
        df_runs.to_excel(writer, sheet_name="runs", index=False)
    print(f"Results saved: {path}")


#-----------------------------------------------------------------------------------------------------------------------
# MEMBERS FILE: per span, criterion, optimum and material variant (see min_max_only) the best feasible member
# best: optimum "GWP" -> lowest co2_struct, optimum "h" -> lowest h_struct; the other value decides a tie
SORT_KEYS = {"GWP": ("co2_struct [kgCO2eq/m2]", "h_struct [m]"), "h": ("h_struct [m]", "co2_struct [kgCO2eq/m2]")}
NO_SECTION = "no feasible section"
COLUMN_BLOCK.update({"candidates (feasible/all)": "identification", "note": "identification"})
# names of list entries in the member attributes (instead of the index), e.g. "fire_bottom" instead of "fire[0]"
# fire: exposed sides of the member (0: no fire, 1: fire), see struct_analysis.Member1D
LIST_LABELS = {"fire": ("bottom", "left", "top", "right")}


def member_attributes(obj, path="", out=None):
    # every attribute of a member (same content and order as the old Members_*.xlsx files), the path is the column
    # name, e.g. "section.concrete_type.fck", "system.alpha_m[0]"; an object gets its class name as value
    if out is None:
        out = {}
    if obj is None or isinstance(obj, (numbers.Number, str)):
        out[path] = obj
    elif isinstance(obj, (list, tuple)):
        labels = LIST_LABELS.get(path)
        for idx, item in enumerate(obj):
            name = f"{path}_{labels[idx]}" if labels and len(labels) == len(obj) else f"{path}[{idx}]"
            member_attributes(item, name, out)
    elif hasattr(obj, "__dict__"):
        if path:
            out[path] = type(obj).__name__
        for attr, value in vars(obj).items():
            member_attributes(value, f"{path}.{attr}" if path else attr, out)
    else:
        out[path] = str(obj)
    return out


def with_identification(row, candidates, note):
    # inserts the columns "candidates (feasible/all)" and "note" after "variant"
    out = {}
    for key, value in row.items():
        out[key] = value
        if key == "variant":
            out.update({"candidates (feasible/all)": candidates, "note": note})
    return out


def best_rows(run, run_rows):
    # one row per span, criterion, optimum and variant: the best feasible member with all its attributes, or a row
    # with the note "no feasible section" if no member of that variant passed all checks
    variants = [v for v in opt_and_plot.VARIANTS if any(row["variant"] == v for row, _ in run_rows)]
    out = []
    for criterion in run["criteria"]:
        for optimum in run["optima"]:
            for length in run["lengths"]:
                for variant in variants:
                    candidates = [(row, entry) for row, entry in run_rows
                                  if (row["criterion"], row["optimum"], row["l_tot [m]"], row["variant"])
                                  == (criterion, optimum, length, variant)]
                    feasible = [(row, entry) for row, entry in candidates if row["feasible"]]
                    count = f"{len(feasible)}/{len(candidates)}"
                    if feasible:
                        row, entry = min(feasible, key=lambda m: tuple(m[0][k] for k in SORT_KEYS[optimum]))
                        out.append({**with_identification(row, count, ""), **member_attributes(entry["member"])})
                    else:
                        out.append(with_identification(
                            {"member_id": None, "criterion": criterion, "optimum": optimum, "variant": variant},
                            count, NO_SECTION) | {"run_nr": run["nr"], "feasible": False, "l_tot [m]": length})
    return out


#-----------------------------------------------------------------------------------------------------------------------
# CHECK RUNS (shows only the runs and stops here if anything is wrong)
batch = prepare_runs(RUNS)
df_runs = runs_table(batch)
print(f"{len(batch)} run(s), all checks passed:")
print(df_runs.drop(columns=["mat_names"]).to_string(index=False))
if CHECK_ONLY:
    raise SystemExit("CHECK_ONLY = True -> no optimization")


#-----------------------------------------------------------------------------------------------------------------------
# OPTIMIZATION
rows = []
failed = []

# Start der Optimierung
start = time.time()

for run in batch:
    print(f"\n=== Run {run['nr']}: {run['label']} ===")
    results = []
    # safety net for unexpected errors during the optimization: the run is reported and the batch continues
    try:
        # retrieve data from database and find optimal cross-sections
        opt_and_plot.plot_dataset(
            run["lengths"], database_name, run["criteria"], run["optima"], get_floor(run["floor"]), req,
            run["crsec_type"], run["mat_names"], run["g2k"], run["qk"], run["max_iter"], len(run["lengths"]) - 1,
            system=run["system"], alg=run["alg"], basetype=run["basetype"],
            results=results, mean_gwp=run["mean_gwp"], members_excel=False,
            min_max_only=run["min_max_only"] and run["basetype"] == "epd")
    except Exception as e:
        traceback.print_exc()
        failed.append((run["nr"], run["label"], repr(e)))
        continue
    if not results:
        failed.append((run["nr"], run["label"], "no products found (check mat_names / basetype)"))
        continue
    # (row, entry) per member: the row for the tables, the entry for the member attributes of the Members file
    rows += [(member_row(entry, run, k), entry) for k, entry in enumerate(results)]

# Ende der Optimierung
dauer = time.time() - start
print(f"\nDie Optimierung dauerte {round(dauer, 2)} Sekunden.")
print(f"{len(batch) - len(failed)} of {len(batch)} run(s) successful.")
for nr, label, err in failed:
    print(f"  FAILED run {nr} ({label}): {err}")


#-----------------------------------------------------------------------------------------------------------------------
# SAVE THE EXCEL FILES: one sheet per run (00, 01, ...), last sheet "runs"; a failed run has no sheet, see status in "runs"
timestamp = datetime.now().strftime("%y%m%d_%H%M")
os.makedirs(results_folder, exist_ok=True)
df_runs["status"] = ["failed" if r["nr"] in [f[0] for f in failed] else "ok" for r in batch]
run_rows = {run["nr"]: [(row, entry) for row, entry in rows if row["run_nr"] == run["nr"]] for run in batch}
# Members file: best member per span and variant
write_excel(os.path.join(results_folder, f"{timestamp}_Members_1D.xlsx"),
            {f"{run['nr']:02d}": best_rows(run, run_rows[run["nr"]]) if run_rows[run["nr"]] else []
             for run in batch}, df_runs)
# batch file (optional): every optimized member
if SAVE_BATCH:
    write_excel(os.path.join(results_folder, f"{timestamp}_batch_1D.xlsx"),
                {f"{run['nr']:02d}": [row for row, _ in run_rows[run["nr"]]] for run in batch}, df_runs)
