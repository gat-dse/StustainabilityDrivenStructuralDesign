# Template_Examples – Summary

## 1. Purpose
`Workflow/261009_Template_Examples.py` runs a batch of 1D optimizations (rc_rec, rc_rib, wd_rec, wd_rib on Simple Beam / Continuous 1D / Two span 1D 1D) and writes the results into **one Excel file per material group** (concrete, wood). Plotting happens later, in a separate step, from these files.

Copy the file and only edit Part 1.

## 2. What you set (Part 1)
- `CHECK_ONLY`: `True` → only check the runs and print the overview, no optimization.
- `DEFAULTS`: values every run uses unless it sets its own: `system`, `basetype` (epd / kbob), `alg`, `max_iter`, `lengths`, `criteria`, `optima`, `g2k`, `qk`.
- `runs`: list of dicts, one per run. Required: `crsec_type`, `floor`. Optional: any key from `DEFAULTS`, plus `mat_names` and `label`.

## 3. What the code does, step by step

**Step 1 – Complete the runs** (`prepare_runs`)
Each run is merged with `DEFAULTS` (run values win). Missing values are filled in:
- `mat_names` from `MATERIALS`, chosen by the prefix of `crsec_type` (rc → ready-mixed concrete, wd → glulam + solid timber).
- `label` built from crsec_type, system, floor, basetype, plus any setting that differs from `DEFAULTS`.

**Step 2 – Check everything before optimizing**
If any check fails, the script prints all errors and stops. Nothing gets optimized.
- *Single run* (`check_run`): no unknown keys; values come from the allowed lists; `lengths` has ≥ 2 positive values in ascending order; `max_iter` is a positive int; loads ≥ 0.
- *Meaningful combinations*: floor fits the section (`ALLOWED_FLOORS`); no `FIRE` for wd_rib (fire is not checked there); only one `optima` for wd_rec (it ignores optima, so more would just repeat datasets).
- *Between runs*: no two runs with identical effective settings (wd ignores `alg`, wd_rec ignores `optima`), no duplicate labels.
- *Database* (`check_database`): for each `basetype` there are products for the main materials, the secondary materials (rebar B500B for rc, plywood boards for wd_rib) and every floor layer.

If two runs would write the same raw Excel name, both get the suffix `_runNN`. The overview table of all runs is printed.

**Step 3 – Build the floor structures** (`get_floor`)
Each floor in `FLOORS` (massiv, Schuettung, Vollholz, Hohlkasten) is read from the database **once** as a `FloorStruc` and then cached. For Hohlkasten, the insulation height `h_ins` lies inside the box, so it is subtracted from `h_Floor`.

**Step 4 – Optimize each run** (`opt_and_plot.plot_dataset(...)`)
For every run:
1. Pick all database products of the chosen materials and `basetype`.
2. Build one initial cross-section per product. For rc this is done twice, with the lowest-GWP and highest-GWP rebar; for wd_rib it is done with the lowest- and highest-GWP board.
3. For every section × criterion × optimum × length: build the static system and a `Member1D` with the loads, then optimize the section (`struct_optimization`, or `struct_optimization_RCrib_cont` for rc_rib on Continuous 1D). wd_rib is optimized once per fixed `t3` case.
4. If no section is feasible (e.g. the span is too long for wd_rec), the member is kept as `feasible = False`.

An unexpected error inside a run is printed, the run is marked `failed`, and the batch continues with the next run.

**Step 5 – Collect and save the results** (`member_row`, `RESULT_FILES`, `SECTION_COLUMNS`)
Each optimized member becomes one row. The results are written into **one Excel per material group**, with **one sheet per cross-section type** (only the types that ran), followed by the sheet `runs`:

| file | sheets |
|---|---|
| `<YYMMDD_HHMM>_batch_concrete.xlsx` | `rc_rec`, `rc_rib`, `runs` |
| `<YYMMDD_HHMM>_batch_wood.xlsx` | `wd_rec`, `wd_rib`, `runs` |

Columns of a sheet, in blocks (order of the supervisor's table; units in brackets; forces in kN, loads in kN/m², CO₂ per m² of floor). Header colors: **green** = configuration / selected data, **yellow** = results, **red** = key results `MEd_n`, `MEd_p`, `VEd`, `co2_struct` (`KEY_COLUMNS`, overrides the block color).

| block | color | all types | rc_rec | rc_rib | wd_rec | wd_rib |
|---|---|---|---|---|---|---|
| identification | – | `member_id`, `criterion`, `optimum` | | | | |
| data source | green | `basetype`, `use` | | | | |
| design configuration | green | `plot_label`, `label`, `run_nr`, `dataset`, `crsec_type`, `system`, `g2k`, `qk`, `feasible` | `alg` | `alg` | | |
| geometry | – | `l_tot`, `h_struct`, `b` | | `b_w`, `h_f` | | `b_w`, `h_rib`, `t2`, `t3` (`h_struct` = h_rib + t2 + t3, `b` = rib spacing) |
| material selection | green | name + `_prod_id` + `_GWP` | `concrete`, `rebar` | `concrete`, `rebar` | `timber` | `timber`, `board` |
| structural results | yellow | `MEd_n`, `MEd_p`, `VEd` | `rebar_content [kg/m3]` | `rebar_content` | | |
| co2 structure | yellow | `co2_struct` | `co2_concrete`, `co2_rebar` | `co2_concrete`, `co2_rebar` | | `co2_rib`, `co2_board` |
| floor build-up | – | `floor`, `h_floor`, `g_floor`, `co2_floor`, `co2_floor_per_year` | | | | |
| final indicators | yellow | `h_tot`, `g_struct`, `g_tot` (dead loads), `co2_tot` | | | | |

`member_id` = `<run in the batch>-<member in the run>`, both counted from 0: the first run gives `00-000`, `00-001`, …, the second `01-000`, … (`run_nr` = run index + 1). `use` (Nutzung, default `"Wohnen"`) is only a label; `qk` has to fit it.
Infeasible spans (`feasible = False`) only have identification, settings, span and materials.
A new material needs one entry in `RESULT_FILES`; a new cross-section type one function in `SECTION_COLUMNS`.

## 4. Output (`Workflow/Results/`)
- One `<YYMMDD_HHMM>_batch_<group>.xlsx` per material group (see above); sheet `runs` holds the settings and status (ok / failed) of the group's runs.
- Raw files per run (written by `plot_dataset`): `Members_{crsec_type}{_simple|_cont|_2span}_{floor}_{basetype}[_runNN].xlsx`.

## 5. How to use
1. Run from inside `Workflow/`: `.venv/bin/python 261009_Template_Examples.py` (databases are opened by relative path).
2. Set `CHECK_ONLY = True` first to see the overview, then set it to `False` and run.

## 6. Good to know
- `alg` only affects concrete sections.
- wd_rib runs twice per product (two `t3` cases); this is intended.
- KBOB has only one rebar (B500B), so it gives fewer datasets than EPD; this is intended.
- **rc_rib GWP is wrong for rib spacings `b ≠ 1 m`** (unit error in `RibbedConcrete`), see `SUMMARY_KBOB_EPD.md` §6.1.
- 2D slabs are not covered (`slab_2d_optimization.py`).

## 7. Possible next steps
- Plot script that reads the `_batch_<group>.xlsx` files (group by `plot_label` / `label`).
- Move Part 2 into a module (e.g. `Workflow/batch_runner.py`) so that the template only holds the settings.
- Resume (skip runs that already have results), parallel runs, and fixed seeds so TPE results can be reproduced.
