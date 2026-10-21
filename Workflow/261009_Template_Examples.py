# TEMPLATE for running examples: 1D members (simple beam / continuous / two span) in reinforced concrete and wood
# with different cross-sections and settings.
#
# HOW TO USE: copy this file and only adjust PART 1 (DEFAULTS and RUNS).
# Before the first optimization starts, all runs are checked (allowed values, allowed combinations, products in the
# database). If anything is wrong, the script stops with a list of all errors and nothing is optimized.
# All runs are written into one combined Excel (Results/<timestamp>_batch.xlsx) and, with PLOT = True, one figure
# (Results/<timestamp>_batch.png).


# ======================================================================================================================
# PART 1: SETTINGS (adjust here)
# ======================================================================================================================

# True: only check the runs and print the overview table, no optimization
CHECK_ONLY = False

# True: draw the figure of all runs, save it as .png and show it; False: only the Excel results
PLOT = True

#-----------------------------------------------------------------------------------------------------------------------
# DEFAULTS: used for every key a run does not set itself
DEFAULTS = {
    "system": "Simple Beam",    # "Simple Beam", "Continuous 1D", "Two span 1D 1D"
    "basetype": "epd",          # data basis: "epd" (product EPDs) or "kbob" (generic KBOB v9.0 values)
    "alg": "TPE",               # rc sections: "basinhoppin" or "TPE" (wd_rec / wd_rib use their own algorithm)
    "max_iter": 50,             # max. number of iterations per optimization. Higher value leads to better results
    "lengths": [4, 6, 8, 10, 12],  # system lengths [m] (datapoints on x-axis of plot), at least 2 values
    "criteria": ["ENV"],        # "ULS", "SLS1" (deflections), "SLS2" (vibrations), "FIRE", "ENV" (all together)
    "optima": ["GWP"],          # "GWP" (min. GWP), "h" (min. height); several possible; wd_rec ignores this
    "g2k": 0.75e3,              # n.t. Einbauten [N/m2]
    "qk": 2e3,                  # Nutzlast [N/m2]
}

#-----------------------------------------------------------------------------------------------------------------------
# RUNS: one entry = one dataset in the plot and in the combined Excel. Comment out entries that are not needed.
# required: "crsec_type" and "floor"
#   crsec_type   floor (allowed combinations, see ALLOWED_FLOORS in part 2)
#   "rc_rec"     "massiv", "Schuettung"
#   "rc_rib"     "Schuettung", "massiv"
#   "wd_rec"     "Vollholz"
#   "wd_rib"     "Hohlkasten"
# optional: every key of DEFAULTS, plus "mat_names" (list), "color" (plot color), "label" (legend / Excel)
runs = [
    {"crsec_type": "rc_rec", "floor": "massiv", "system": "Simple Beam", "basetype": "epd"},
    # {"crsec_type": "rc_rec", "floor": "massiv", "system": "Simple Beam", "basetype": "kbob", "color": "blue"},
    # {"crsec_type": "rc_rec", "floor": "massiv", "system": "Continuous 1D"},
    # {"crsec_type": "rc_rib", "floor": "Schuettung", "system": "Simple Beam"},
    # {"crsec_type": "rc_rib", "floor": "Schuettung", "system": "Continuous 1D"},
    # {"crsec_type": "wd_rec", "floor": "Vollholz", "system": "Simple Beam"},
    # {"crsec_type": "wd_rib", "floor": "Hohlkasten", "system": "Simple Beam"},
    # {"crsec_type": "rc_rec", "floor": "massiv", "alg": "basinhoppin", "color": "red"},
]


# ======================================================================================================================
# PART 2: FIXED DEFINITIONS AND PROGRAM CODE
# Not meant to be changed for running optimizations. Change only to extend the template itself
# (e.g. a new floor structure, a new material or a new allowed combination).
# ======================================================================================================================

# IMPORT
import struct_analysis  # file with code for structural analysis
import opt_and_plot  # file with code for optimization and plotting results in a standardized way
import matplotlib.pyplot as plt
from matplotlib.colors import is_color_like
from matplotlib.lines import Line2D
import pandas as pd
import sqlite3
import os
import time
import traceback
from datetime import datetime

database_name = "database_261009.db"
results_folder = "Results"

# define service limit state criteria
req = struct_analysis.Requirements()

#-----------------------------------------------------------------------------------------------------------------------
# FLOOR STRUCTURES (non load bearing layers: [product name, thickness or False for default, False])
# The name is used in the Excel file name, the plot colors and the combined result table.
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
ALLOWED_KEYS = set(DEFAULTS) | {"crsec_type", "floor", "mat_names", "color", "label"}


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


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
    if "color" in entry and not is_color_like(entry["color"]):
        err.append(f"color {entry['color']!r} is not a matplotlib color")
    return err


def check_database(batch):
    # returns error messages for products the runs need but the database does not contain
    err = []
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    checked = set()
    for run in batch:
        base, crsec = run["basetype"], run["crsec_type"]
        # main materials (same query as plot_dataset)
        for mat_name in run["mat_names"]:
            if (mat_name, base) in checked:
                continue
            checked.add((mat_name, base))
            cursor.execute("SELECT COUNT(*) FROM products WHERE DENSITY IS NOT NULL AND MECH_PROP IS NOT NULL"
                           " AND \"MATERIAL\" LIKE " + mat_name + opt_and_plot.source_filter(base))
            if cursor.fetchone()[0] == 0:
                err.append(f"run {run['nr']}: no product for material {mat_name} with basetype {base!r}")
        # secondary materials: rebar for rc, boards for wd_rib (same queries as plot_dataset)
        extra = {"rc": ("Steel_reinforcing_bar", "B500B"), "wd_rib": ("%3_and_5_plywood%", None)}
        key = crsec[:2] if crsec[:2] == "rc" else crsec
        if key in extra and (key, base) not in checked:
            checked.add((key, base))
            try:
                opt_and_plot.get_low_high_prod_ids(cursor, *extra[key], base)
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
    # settings that really change the result (wd ignores alg, wd_rec ignores optima)
    return (run["crsec_type"], run["system"], run["floor"], run["basetype"], run["max_iter"], tuple(run["lengths"]),
            tuple(run["criteria"]), tuple(run["mat_names"]), run["g2k"], run["qk"],
            None if run["crsec_type"][:2] == "wd" else run["alg"],
            None if run["crsec_type"] == "wd_rec" else tuple(run["optima"]))


def prepare_runs(runs):
    # completes all runs with DEFAULTS and checks them; stops the script if any check fails
    if not runs:
        raise SystemExit("No runs defined -> activate at least one entry in RUNS.")
    batch, errors = [], []
    for i, entry in enumerate(runs, start=1):
        run = {**DEFAULTS, **entry}
        run_errors = check_run(i, entry, run)
        errors += [f"run {i}: {e}" for e in run_errors]
        if run_errors:
            continue
        run["nr"] = i
        run.setdefault("mat_names", MATERIALS[run["crsec_type"][:2]])
        # default label: main keys + every other setting that differs from DEFAULTS
        extra = [f"{k}={entry[k]}" for k in ("alg", "max_iter", "lengths", "criteria", "optima", "g2k", "qk")
                 if k in entry and entry[k] != DEFAULTS[k]]
        run.setdefault("label", ", ".join([run["crsec_type"], run["system"], run["floor"], run["basetype"]] + extra))
        batch.append(run)

    # combinations between runs
    for a_idx, a in enumerate(batch):
        for b in batch[a_idx + 1:]:
            if effective_key(a) == effective_key(b):
                errors.append(f"runs {a['nr']} and {b['nr']} give the same result (identical effective settings)")
            if a["label"] == b["label"]:
                errors.append(f"runs {a['nr']} and {b['nr']} have the same label {a['label']!r}")

    if not errors:
        errors += check_database(batch)
    if errors:
        print("\nINVALID RUNS - nothing was optimized:\n  " + "\n  ".join(errors))
        raise SystemExit(1)

    # runs with the same Excel file name in plot_dataset get a suffix, so they do not overwrite each other
    name_key = lambda r: (r["crsec_type"], r["system"], r["floor"], r["basetype"])
    for run in batch:
        same_name = sum(name_key(r) == name_key(run) for r in batch)
        run["file_tag"] = f"_run{run['nr']:02d}" if same_name > 1 else ""
    return batch


def runs_table(batch):
    cols = ["nr", "label", "crsec_type", "system", "floor", "basetype", "alg", "max_iter", "lengths", "criteria",
            "optima", "g2k", "qk", "mat_names", "file_tag"]
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
# COMBINED RESULT TABLE: one row per optimized member
def member_row(entry, run):
    mem = entry["member"]
    sec = mem.section if mem is not None else entry["section_0"]
    if hasattr(sec, "concrete_type"):
        mat_1, mat_2 = sec.concrete_type, sec.rebar_type
    elif hasattr(sec, "wood_type_1"):  # wd_rib: rib timber + board
        mat_1, mat_2 = sec.wood_type_1, getattr(sec, "wood_type_2", None)
    else:
        mat_1, mat_2 = getattr(sec, "wood_type", None), None
    row = {
        "run_nr": run["nr"], "label": run["label"],
        "plot_label": f"{run['system']}_{run['crsec_type']}_{run['floor']}_{run['basetype']}",
        "crsec_type": run["crsec_type"], "system": run["system"], "floor": run["floor"],
        "basetype": run["basetype"], "alg": run["alg"], "max_iter": run["max_iter"],
        "criterion": entry["criterion"], "optimum": entry["optimum"], "t3": entry["t3"],
        "g2k [N/m2]": run["g2k"], "qk [N/m2]": run["qk"], "dataset": entry["dataset"],
        "l_tot [m]": entry["length"], "feasible": mem is not None,
        "mat_1": getattr(mat_1, "mech_prop", None), "prod_id_1": getattr(mat_1, "prod_id", None),
        "GWP_1 [kgCO2eq/kg]": getattr(mat_1, "GWP", None),
        "mat_2": getattr(mat_2, "mech_prop", None), "prod_id_2": getattr(mat_2, "prod_id", None),
        "GWP_2 [kgCO2eq/kg]": getattr(mat_2, "GWP", None),
    }
    if mem is not None:
        row.update({
            "h_struct [m]": mem.section.h, "b [m]": mem.section.b,
            "h_floor [m]": mem.floorstruc.h_Floor, "h_tot [m]": mem.section.h + mem.floorstruc.h_Floor,
            "co2_struct [kgCO2eq/m2]": mem.section.co2, "co2_floor [kgCO2eq/m2]": mem.floorstruc.co2_Floor,
            "co2_tot [kgCO2eq/m2]": mem.section.co2 + mem.floorstruc.co2_Floor,
            "MEd_n [kNm]": mem.mEd_n / 1e3, "MEd_p [kNm]": mem.mEd_p / 1e3, "VEd [kN]": mem.vEd / 1e3,
        })
    return row


#-----------------------------------------------------------------------------------------------------------------------
# CHECK RUNS (stops here if anything is wrong)
batch = prepare_runs(runs)
df_runs = runs_table(batch)
print(f"{len(batch)} run(s), all checks passed:")
print(df_runs.drop(columns=["mat_names"]).to_string(index=False))
if CHECK_ONLY:
    raise SystemExit("CHECK_ONLY = True -> no optimization")


#-----------------------------------------------------------------------------------------------------------------------
# OPTIMIZATION
def max_of_arrays(existing_data, new_data):
    return [max(a, b) for a, b in zip(existing_data, new_data)]


data_max = [0, 0, 0, 0]
vrfctn_members = []
rows = []
failed = []
legend_handles = []

# Start der Optimierung
start = time.time()

for run in batch:
    print(f"\n=== Run {run['nr']}: {run['label']} ===")
    results = []
    n_lines = len(plt.figure(1).axes[0].lines) if PLOT and plt.figure(1).axes else 0
    # safety net for unexpected errors during the optimization: the run is reported and the batch continues
    try:
        # retrieve data from database, find optimal cross-sections and plot results
        data_max_new, vrfctn_members_new = opt_and_plot.plot_dataset(
            run["lengths"], database_name, run["criteria"], run["optima"], get_floor(run["floor"]), req,
            run["crsec_type"], run["mat_names"], run["g2k"], run["qk"], run["max_iter"], len(run["lengths"]) - 1,
            system=run["system"], alg=run["alg"], basetype=run["basetype"],
            results=results, color=run.get("color"), file_tag=run["file_tag"], plot=PLOT)
    except Exception as e:
        traceback.print_exc()
        failed.append((run["nr"], run["label"], repr(e)))
        continue
    if not results:
        failed.append((run["nr"], run["label"], "no products found (check mat_names / basetype)"))
        continue
    data_max = max_of_arrays(data_max, data_max_new)
    vrfctn_members.append(vrfctn_members_new)
    rows += [member_row(entry, run) for entry in results]
    # legend entry with the color plot_dataset used for this run
    if PLOT and plt.figure(1).axes and len(plt.figure(1).axes[0].lines) > n_lines:
        legend_handles.append(Line2D([0], [0], color=plt.figure(1).axes[0].lines[-1].get_color(), label=run["label"]))

# Ende der Optimierung
dauer = time.time() - start
print(f"\nDie Optimierung dauerte {round(dauer, 2)} Sekunden.")
print(f"{len(batch) - len(failed)} of {len(batch)} run(s) successful.")
for nr, label, err in failed:
    print(f"  FAILED run {nr} ({label}): {err}")


#-----------------------------------------------------------------------------------------------------------------------
# SAVE COMBINED EXCEL (sheet "members": one row per member, sheet "runs": settings of all runs)
timestamp = datetime.now().strftime("%y%m%d_%H%M")
os.makedirs(results_folder, exist_ok=True)
if rows:
    excel_path = os.path.join(results_folder, f"{timestamp}_batch.xlsx")
    df_runs["status"] = ["failed" if r["nr"] in [f[0] for f in failed] else "ok" for r in batch]
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="members", index=False)
        df_runs.to_excel(writer, sheet_name="runs", index=False)
    print(f"Combined results saved: {excel_path}")


#-----------------------------------------------------------------------------------------------------------------------
# PLOT (only with PLOT = True)
if PLOT:
    # DEFINE LABELS OF PLOTS
    plotted_data = [["h$_{struct}$", "[m]"], ["h$_{tot}$", "[m]"], ["GWP$_{struct}$", "[kg-CO$_2$-eq]"], ["GWP$_{tot}$", "[kg-CO$_2$-eq]"]]
    all_lengths = [l for run in batch for l in run["lengths"]]

    # ADD LABELS, LEGEND, AXIS LIMITS AND GRID TO THE PLOTS
    plt.figure(1)
    for idx, info in enumerate(plotted_data):
        plt.subplot(2, 2, idx + 1)
        plt.xlabel('l [m]', fontsize=12)
        plt.ylabel(info[0] + " " + info[1], fontsize=12)
        if idx % 2 == 0:
            plt.axis((min(all_lengths), max(all_lengths), 0, max(data_max[idx], data_max[idx+1])))
        else:
            plt.axis((min(all_lengths), max(all_lengths), 0, max(data_max[idx], data_max[idx-1])))
        plt.grid()
    if legend_handles:
        plt.figure(1).legend(handles=legend_handles, loc="lower center", ncol=2, fontsize=8)
        plt.subplots_adjust(bottom=0.14 + 0.04 * ((len(legend_handles) + 1) // 2), hspace=0.35, wspace=0.35)

    # # plot cross-section of members for verification
    # for mem_group in vrfctn_members:
    #     for i, mem in enumerate(mem_group[0]):
    #         opt_and_plot.plot_section(mem.section)
    #         plt.title(f'#{mem_group[1][i]}')

    # SAVE AND SHOW FIGURE
    if rows:
        plt.figure(1).savefig(os.path.join(results_folder, f"{timestamp}_batch.png"), dpi=200)
    plt.show()

