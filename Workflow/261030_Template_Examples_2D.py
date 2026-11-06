# TEMPLATE for running examples (1D members: 261030_Template_Examples_1D.py): 2D square reinforced concrete slabs
# (rc_rec) with different supports and settings.
#
# HOW TO USE: copy this file and only adjust PART 1 (DEFAULTS and RUNS).
# Before the first optimization starts, all runs are checked (allowed values, allowed combinations, products and spans
# in the database). If anything is wrong, the script stops with a list of all errors and nothing is optimized.
# The results are written into one Excel (Results/<timestamp>_batch_2D.xlsx): one sheet per run (00, 01, ...) and the
# sheet "runs". Plotting is done separately.


# ======================================================================================================================
# PART 1: SETTINGS (adjust here)
# ======================================================================================================================

# True: only check the runs and print the overview table, no optimization
CHECK_ONLY = False

#-----------------------------------------------------------------------------------------------------------------------
# DEFAULTS: used for every key a run does not set itself
DEFAULTS = {
    "support": "LL-frei",       # "LL-frei", "LL-eingespannt", "PL-eingespannt"
    "basetype": "epd",          # data basis: "epd" (product EPDs) or "kbob" (generic KBOB v9.0 values)
    "alg": "TPE",               # "TPE" or "basinhoppin"
    "max_iter": 800,            # max. number of iterations per optimization (TPE: 50 gives far too high GWP, 800 is close to converged)
    "lengths": [3, 5, 6, 8, 10],  # slab spans [m] (square slabs, lx = ly), at least 2 values from the database:
                                # 3, 4, 5, 6, 7, 8, 10, 12, 16 (PL-eingespannt: no 4)
    "criteria": ["ENV"],        # "ULS", "SLS1" (deflections), "SLS2" (vibrations), "FIRE", "ENV" (all together)
    "optima": ["GWP"],          # "GWP" (min. GWP), "h" (min. height); several possible
    "g2k": 0.75e3,              # n.t. Einbauten [N/m2]
    "qk": 2e3,                  # Nutzlast [N/m2]
    "use": "Wohnen",            # building use (Nutzung), only a label in the results; qk must fit it
    "min_max_only": True,       # True: only products with MIN_MAX = 1 in the database (lowest and highest GWP of
                                # each strength class); False: all products. Rebar, boards and mean sections
                                # are not affected; only for basetype "epd", ignored for "kbob"
    "mean_gwp": True,           # True: additional "mean sections": one per strength class of concrete, with the mean
                                # GWP and mean density of all products of that class, rebar (B500B) is a mean as well;
                                # only for basetype "epd", ignored for "kbob"
}

#-----------------------------------------------------------------------------------------------------------------------
# RUNS: Set the parameters you want to use
# floor: "massiv", "Schuettung"
RUNS = [
    {"support": "LL-frei", "floor": "massiv"},
    {"support": "LL-eingespannt", "floor": "massiv"},
    {"support": "PL-eingespannt", "floor": "massiv"},
]


# ======================================================================================================================
# PART 2: FIXED DEFINITIONS AND PROGRAM CODE
# Not meant to be changed for running optimizations. Change only to extend the template itself
# (e.g. a new floor structure or a new allowed combination).
# ======================================================================================================================

# IMPORT
import struct_analysis  # file with code for structural analysis
import opt_and_plot  # file with the shared product selection
import plot_datasets_2D  # file with code for optimization and plotting results in a standardized way
import pandas as pd
import sqlite3
import os
import time
import traceback
from datetime import datetime
from openpyxl.styles import PatternFill

database_name = "database_261009.db"
slab_database_name = "260625_slab_properties.db"
results_folder = "Results"

# define service limit state criteria
req = struct_analysis.Requirements()

#-----------------------------------------------------------------------------------------------------------------------
# FLOOR STRUCTURES (non load bearing layers: [product name, thickness or False for default, False])
# The name is used in the result tables and selects the minimum height for sound insulation in the optimization.
FLOORS = {
    # solid reinforced concrete cross-section
    "massiv": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
               ["'Unterlagsboden Zement, 85 mm'", False, False],
               ["'Glaswolle'", 0.03, False]],
    # with additional gravel
    "Schuettung": [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                   ["'Unterlagsboden Zement, 85 mm'", False, False],
                   ["'Glaswolle'", 0.03, False], ["'Kies gebrochen'", 0.06, False]],
}

#-----------------------------------------------------------------------------------------------------------------------
# MATERIALS (table products, attribute material)
CRSEC_TYPE = "rc_rec"  # the only cross-section type of the 2D optimization
MAT_NAMES = ["'ready_mixed_concrete'"]

#-----------------------------------------------------------------------------------------------------------------------
# ALLOWED VALUES
SUPPORTS = ["LL-frei", "LL-eingespannt", "PL-eingespannt"]
BASETYPES = ["epd", "kbob"]
ALGS = ["TPE", "basinhoppin"]
CRITERIA = ["ULS", "SLS1", "SLS2", "FIRE", "ENV"]
OPTIMA = ["GWP", "h"]
ALLOWED_KEYS = set(DEFAULTS) | {"floor", "label"}


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) # returns true for int & float


def check_run(entry, run):
    # returns a list of error messages for one run (empty list: run is valid)
    err = []
    unknown = set(entry) - ALLOWED_KEYS
    if unknown:
        err.append(f"unknown key(s) {sorted(unknown)}; allowed: {sorted(ALLOWED_KEYS)}")
    if run.get("floor") not in FLOORS:
        err.append(f"floor must be one of {list(FLOORS)}, got {run.get('floor')!r}")
    if run["support"] not in SUPPORTS:
        err.append(f"support must be one of {SUPPORTS}, got {run['support']!r}")
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
    return err


def check_database(batch):
    # adds error messages into the error vector if there are products or spans the runs need but the databases do not
    # contain
    err = []
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    for base, min_max_only in sorted({(run["basetype"], run["min_max_only"] and run["basetype"] == "epd") for run in batch}):
        for mat_name in MAT_NAMES:  # same query as plot_dataset
            cursor.execute("SELECT COUNT(*) FROM products WHERE DENSITY IS NOT NULL AND MECH_PROP IS NOT NULL"
                           " AND \"MATERIAL\" LIKE " + mat_name + opt_and_plot.source_filter(base)
                           + opt_and_plot.min_max_filter(min_max_only))
            if cursor.fetchone()[0] == 0:
                err.append(f"no product for material {mat_name} with basetype {base!r}, min_max_only={min_max_only}")
        try:
            opt_and_plot.get_low_high_prod_ids(cursor, "Steel_reinforcing_bar", "B500B", base)
        except ValueError as e:
            err.append(str(e))
    connection.close()
    # spans: every combination of support and span must be in the slab table
    connection = sqlite3.connect(slab_database_name)
    cursor = connection.cursor()
    for run in batch:
        for length in run["lengths"]:
            cursor.execute("SELECT COUNT(*) FROM slab_properties WHERE RAENDER = ? AND LX = ? AND LY = ?",
                           (run["support"], length, length))
            if cursor.fetchone()[0] == 0:
                err.append(f"run {run['nr']}: no slab data for support {run['support']!r}, span {length} m")
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
    # ignored settings are set to False: min_max_only and mean_gwp for kbob
    return (run["support"], run["floor"], run["basetype"], run["alg"], run["max_iter"], tuple(run["lengths"]),
            tuple(run["criteria"]), tuple(run["optima"]), run["g2k"], run["qk"],
            run["min_max_only"] and run["basetype"] == "epd", run["mean_gwp"] and run["basetype"] == "epd")


def prepare_runs(runs):
    # completes all runs with DEFAULTS and checks them; stops the script if any check fails
    if not runs:
        raise SystemExit("No runs defined -> activate at least one entry in RUNS.")
    batch, errors = [], []
    for i, entry in enumerate(runs):  # runs are counted from 0
        run = {**DEFAULTS, **entry}
        run_errors = check_run(entry, run)
        errors += [f"run {i}: {e}" for e in run_errors]
        if run_errors:
            continue
        run["nr"] = i
        # default label: main keys + every other setting that differs from DEFAULTS
        extra = [f"{k}={entry[k]}" for k in ("alg", "max_iter", "lengths", "criteria", "optima", "g2k", "qk", "use", "min_max_only",
                                  "mean_gwp")
                 if k in entry and entry[k] != DEFAULTS[k]]
        run.setdefault("label", ", ".join([run["support"], run["floor"], run["basetype"]] + extra))
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

    # file_tag: suffix for the Members_2D_*.xlsx file that plot_dataset writes per run.
    # that file name only contains support and basetype -> runs sharing these get "_run00", "_run01"... so they do not overwrite each other
    name_key = lambda r: (r["support"], r["basetype"])
    for run in batch:
        same_name = sum(name_key(r) == name_key(run) for r in batch)
        run["file_tag"] = f"_run{run['nr']:02d}" if same_name > 1 else ""
    return batch


def runs_table(batch):
    cols = ["nr", "label", "support", "floor", "basetype", "alg", "max_iter", "lengths", "criteria",
            "optima", "g2k", "qk", "use", "min_max_only", "mean_gwp", "file_tag"]
    return pd.DataFrame([{c: (str(r[c]) if isinstance(r[c], list) else r[c]) for c in cols} for r in batch])


#-----------------------------------------------------------------------------------------------------------------------
# FLOOR OBJECTS (each floor is read from the database once)
_floor_cache = {}


def get_floor(name):
    if name not in _floor_cache:
        _floor_cache[name] = struct_analysis.FloorStruc(FLOORS[name], database_name, name=name)
    return _floor_cache[name]


#-----------------------------------------------------------------------------------------------------------------------
# RESULT TABLES: one Excel with one sheet per run
# Column blocks of a sheet: identification | settings | geometry | internal forces | materials | CO2 | loads
def material_columns(role, mat):
    return {role: getattr(mat, "mech_prop", None), f"{role}_prod_id": getattr(mat, "prod_id", None),
            f"{role}_GWP [kgCO2eq/kg]": getattr(mat, "GWP", None)}


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
    geo = {}
    if mem is not None:
        (di_xu, s_xu), (di_xo, s_xo), (di_yu, s_yu), (di_yo, s_yo) = sec.bw
        geo = {"h_struct [m]": sec.h, "b [m]": sec.b,
               "di_xu [m]": di_xu, "s_xu [m]": s_xu, "di_xo [m]": di_xo, "s_xo [m]": s_xo,
               "di_yu [m]": di_yu, "s_yu [m]": s_yu, "di_yo [m]": di_yo, "s_yo [m]": s_yo}
    blocks = {
        # member_id = <run in the batch>-<member in the run>, both counted from 0 (first member: 00-000)
        "identification": {"member_id": f"{run['nr']:02d}-{k:03d}", "criterion": entry["criterion"],
                           "optimum": entry["optimum"]},
        "data source": {"basetype": run["basetype"], "use": run["use"]},
        "design configuration": {
            "plot_label": f"2D_{run['support']}_{CRSEC_TYPE}_{run['floor']}_{run['basetype']}",
            "label": run["label"], "run_nr": run["nr"], "dataset": entry["dataset"],
            "crsec_type": CRSEC_TYPE, "support": run["support"], "alg": run["alg"],
            "g2k [kN/m2]": run["g2k"] / 1e3, "qk [kN/m2]": run["qk"] / 1e3, "feasible": not entry["failed_checks"],
            "failed_checks": ", ".join(entry["failed_checks"])},
        "geometry": {"l_tot [m]": entry["length"], **geo},
        "material selection": {"mean_section": entry["mean_section"],
                               **material_columns("concrete", sec.concrete_type),
                               **material_columns("rebar", sec.rebar_type)},
    }
    if mem is not None:
        fl = mem.floorstruc
        g_struct = sec.g0k / sec.b / 1e3
        co2_struct = sec.co2 / sec.b
        blocks["structural results"] = {
            "rebar_content [kg/m3]": sec.Bew_Gehalt,
            "MEd_n [kNm]": mem.mEd_n / 1e3, "MEd_p [kNm]": mem.mEd_p / 1e3, "VEd [kN]": mem.vEd / 1e3}
        blocks["co2 structure"] = {"co2_concrete [kgCO2eq/m2]": sec.co2_concrete / sec.b,
                                   "co2_rebar [kgCO2eq/m2]": sec.co2_rebar / sec.b,
                                   "co2_struct [kgCO2eq/m2]": co2_struct}
        blocks["floor build-up"] = {
            "floor": run["floor"], "h_floor [m]": fl.h_Floor, "g_floor [kN/m2]": fl.gk_area / 1e3,
            "co2_floor [kgCO2eq/m2]": fl.co2_Floor, "co2_floor_per_year [kgCO2eq/m2a]": fl.co2_a_Floor}
        blocks["final indicators"] = {
            "h_tot [m]": sec.h + fl.h_Floor, "g_struct [kN/m2]": g_struct,
            "g_tot [kN/m2]": g_struct + fl.gk_area / 1e3,
            "co2_tot [kgCO2eq/m2]": co2_struct + fl.co2_Floor}
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


#-----------------------------------------------------------------------------------------------------------------------
# CHECK RUNS (shows only the runs and stops here if anything is wrong)
batch = prepare_runs(RUNS)
df_runs = runs_table(batch)
print(f"{len(batch)} run(s), all checks passed:")
print(df_runs.to_string(index=False))
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
        plot_datasets_2D.plot_dataset(
            run["lengths"], run["lengths"], [run["support"]], database_name, run["criteria"], run["optima"],
            get_floor(run["floor"]), req, CRSEC_TYPE, MAT_NAMES, run["g2k"], run["qk"], run["max_iter"],
            len(run["lengths"]) - 1, basetype=run["basetype"], alg=run["alg"], results=results,
            file_tag=run["file_tag"], mean_gwp=run["mean_gwp"],
            min_max_only=run["min_max_only"] and run["basetype"] == "epd")
    except Exception as e:
        traceback.print_exc()
        failed.append((run["nr"], run["label"], repr(e)))
        continue
    if not results:
        failed.append((run["nr"], run["label"], "no products found (check basetype)"))
        continue
    rows += [member_row(entry, run, k) for k, entry in enumerate(results)]

# Ende der Optimierung
dauer = time.time() - start
print(f"\nDie Optimierung dauerte {round(dauer, 2)} Sekunden.")
print(f"{len(batch) - len(failed)} of {len(batch)} run(s) successful.")
for nr, label, err in failed:
    print(f"  FAILED run {nr} ({label}): {err}")


#-----------------------------------------------------------------------------------------------------------------------
# SAVE ONE EXCEL: one sheet per run (00, 01, ...), last sheet "runs"; a failed run has no sheet, see status in "runs"
timestamp = datetime.now().strftime("%y%m%d_%H%M")
os.makedirs(results_folder, exist_ok=True)
df_runs["status"] = ["failed" if r["nr"] in [f[0] for f in failed] else "ok" for r in batch]
excel_path = os.path.join(results_folder, f"{timestamp}_batch_2D.xlsx")
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    for run in batch:
        sheet_rows = [r for r in rows if r["run_nr"] == run["nr"]]
        if not sheet_rows:
            continue
        # column order of the longest row (feasible member); infeasible rows only miss the result columns
        columns = max((list(r) for r in sheet_rows), key=len)
        write_sheet(writer, f"{run['nr']:02d}", pd.DataFrame(sheet_rows, columns=columns))
    df_runs.to_excel(writer, sheet_name="runs", index=False)
print(f"Results saved: {excel_path}")
