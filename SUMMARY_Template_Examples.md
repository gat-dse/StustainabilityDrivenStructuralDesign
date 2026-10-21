# Summary: `Workflow/261009_Template_Examples.py` (updated 2026-10-18)

EPD/KBOB background and open problems: `archive/261018_cleanup_and_database/SUMMARY_KBOB_EPD.md`.

## 1. Purpose
Template for running 1D examples (rc_rec, rc_rib, wd_rec, wd_rib; Simple Beam / Continuous 1D / Two span 1D 1D) with different setups in one batch. Copy the file and adjust only Part 1. All runs end up in one combined Excel and, optionally, one figure.

## 2. Structure
**Part 1 – Settings (adjust here)**
- `CHECK_ONLY`: only check the runs and print the overview table, no optimization.
- `PLOT`: draw, save (`.png`) and show the figure of all runs; `False` → only Excel.
- `DEFAULTS`: `system`, `basetype` (epd/kbob), `alg`, `max_iter`, `lengths`, `criteria`, `optima`, `g2k`, `qk`.
- `runs`: one dict per run. Required: `crsec_type`, `floor`. Optional: every key of `DEFAULTS`, plus `mat_names`, `color`, `label`. Missing keys come from `DEFAULTS`.

**Part 2 – Fixed definitions and program code (not changed for normal use)**
- Imports, `database_name`, `results_folder`, `Requirements()`.
- `FLOORS` (massiv, Schuettung, Vollholz, Hohlkasten) + `FLOOR_H_CORRECTION` (Hohlkasten: insulation `h_ins` lies within the box), `MATERIALS` (rc / wd).
- Allowed values and combinations: `SYSTEMS`, `BASETYPES`, `ALGS`, `CRITERIA`, `OPTIMA`, `ALLOWED_FLOORS`.
- Checks (`check_run`, `check_database`, `prepare_runs`), overview table, floor cache, row builder for the combined table.
- Optimization loop, Excel export, plot (only with `PLOT = True`).

## 3. Checks before the start
If any check fails, the script stops with a list of all errors and nothing is optimized.
- Per run: unknown keys, allowed values, `lengths` (≥ 2 positive values, ascending), `max_iter` (positive int), loads ≥ 0, valid matplotlib color.
- Combinations: floor must fit the section (`ALLOWED_FLOORS`: rc_rec → massiv/Schuettung, rc_rib → Schuettung/massiv, wd_rec → Vollholz, wd_rib → Hohlkasten); wd_rib + `FIRE` (fire not checked); wd_rec + several `optima` (ignored → repeated datasets).
- Between runs: identical effective settings (wd ignores `alg`, wd_rec ignores `optima`), duplicate labels.
- Database: all main materials, rebar (rc) / boards (wd_rib) and floor products exist for the chosen `basetype`.

Tested 2026-10-18: all crsec_type × system × basetype combinations and all crsec_type × floor combinations run technically. The combination rules exclude meaningless results, not crashes.

During the optimization, an unexpected error in one run is printed, the run is marked `failed`, and the batch continues.

## 4. Output (in `Results/` relative to the working directory)
- `<YYMMDD_HHMM>_batch.xlsx`:
  - sheet `members`: one row per optimized member (incl. infeasible spans with `feasible = False`); run settings (`basetype`, `alg`, `criterion`, loads, …), span, materials + prod_id + GWP, heights, CO₂ (structure, floor, total), MEd/VEd, `plot_label`.
  - sheet `runs`: settings and status (ok/failed) of every run.
- `<YYMMDD_HHMM>_batch.png` (only with `PLOT = True`), legend with one entry per run.
- Raw files per run as before: `Members_{crsec_type}{_simple|_cont|_2span}_{floor}_{basetype}.xlsx`. If two runs would get the same name, both get a suffix `_runNN`.

## 5. Changes in `Workflow/opt_and_plot.py` (`plot_dataset`)
New optional kwargs, defaults keep the old behaviour (the older input scripts work unchanged):
- `results`: list, one entry per optimized member is appended (member, length, criterion, optimum, t3).
- `color`: overrides the line color chosen from section type / system / floor.
- `file_tag`: suffix of the raw Excel file name.
- `plot`: `False` → nothing is drawn; results, `data_max` and Excel are still created.

## 6. How to use
- Run from inside `Workflow/` with `.venv/bin/python 261009_Template_Examples.py` (databases are opened by relative path).
- First set `CHECK_ONLY = True` to see the overview table, then `False` to run.

## 7. Issues to know about
- **Colors:** runs that differ only in `alg`, `max_iter` or loads get the same default color → set `color` per run.
- **Shading of the bands looks almost opaque:** `plot_dataset` draws the band again for every member (pre-existing).
- **`rc_rib` GWP is wrong for rib spacings `b ≠ 1 m`** (unit error in `RibbedConcrete`), see `SUMMARY_KBOB_EPD.md`, Section 6.1.
- **Verification plot crashes for `wd_rib`** (`NameError` in `plot_wd_rib_with_dimensions`) if the commented `plot_section` loop is activated, see `SUMMARY_KBOB_EPD.md`, Section 6.2.
- **`alg` only affects concrete sections**; `Continuous 1D` + `rc_rib` uses `struct_optimization_RCrib_cont.py`.
- **`wd_rib` runs twice per product** (`t3` in `T_KANDIDATEN_WDRIB`), intended.
- **KBOB has only one rebar (B500B)** → fewer datasets than EPD, intended.
- **`Results/Members_to_single_db.py`** (old merge step) still works on the raw files but skips wood and has no `basetype` column; the combined batch Excel replaces it for new runs.
- **2D slabs are not covered** (`slab_2d_optimization.py` / `plot_datasets_2D.py`).

## 8. Possible next steps
- Move Part 2 into a module (e.g. `Workflow/batch_runner.py`) so the template is only the settings (~60 lines).
- Skip runs whose results already exist (resume), parallel runs, fixed seeds for reproducible TPE results.
