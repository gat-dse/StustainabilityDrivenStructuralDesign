# Template_Examples – Summary

## 1. Purpose
`Workflow/261009_Template_Examples.py` runs a batch of 1D optimizations (rc_rec, rc_rib, wd_rec, wd_rib on Simple Beam / Continuous 1D / Two span 1D 1D) and writes the results into **one Excel file per material group** (concrete, wood). Plotting happens later, in a separate step, from these files.

Copy the file and only edit Part 1.

## 2. What you set (Part 1)
- `CHECK_ONLY`: `True` → only check the runs and print the overview, no optimization.
- `DEFAULTS`: values every run uses unless it sets its own: `system`, `basetype` (epd / kbob), `alg`, `max_iter`, `lengths`, `criteria`, `optima`, `g2k`, `qk`, `use` (Nutzung, label only), `mean_gwp` (mean section on/off, see §4).
- `RUNS`: list of dicts, one per run. Required: `crsec_type`, `floor`. Optional: any key from `DEFAULTS`, plus `mat_names` and `label`.
  Not every combination is allowed (`ALLOWED_FLOORS`): rc_rec / rc_rib → `massiv`, `Schuettung`; wd_rec → `Vollholz`; wd_rib → `Hohlkasten`. Names are case-sensitive.

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
3. With `mean_gwp = True` and `basetype = "epd"`: add **one mean section** per run (see §4).
4. For every section × criterion × optimum × length: build the static system and a `Member1D` with the loads, then optimize the section (`struct_optimization`, or `struct_optimization_RCrib_cont` for rc_rib on Continuous 1D). wd_rib is optimized once per fixed `t3` case (0.027 m and 0.04 m).
5. If no section is feasible (e.g. the span is too long for wd_rec), the member is kept as `feasible = False`.
6. Template only: for the wd_rib mean section, only the worse `t3` case is kept (`keep_worse_t3`, see §4).

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
The mean section is marked with `mean_section = True` (block material selection).

## 4. Mean section (`mean_gwp`)

### 4.1 Goal
Besides all products of a material, every run (EPD) gets **exactly one additional cross-section that represents the average material**. To stay scientifically valid, **no values are invented**: instead of averaging properties, the code picks the **real product** whose GWP is closest to the mean and uses all of its own properties (strength, density, GWP) from the database. Where a choice remains (the `t3` case of wd_rib), the **conservative (worse) case** is kept.

### 4.2 Rules
| material of the run | products used for the mean | mean section uses |
|---|---|---|
| concrete (rc) | all EPD products of `ready_mixed_concrete` (same as the normal loop) | product closest to the mean |
| timber (wd) | all EPD products of **all** `mat_names` of the run **pooled** (glulam + solid timber) | product closest to the mean |
| rebar (rc) | all EPD B500B rebars | product closest to the mean |
| board (wd_rib) | all EPD `3_and_5_plywood` products | product closest to the mean |

- **Mean** = arithmetic mean of the GWP values of all products (not (min + max) / 2).
- **Closest**: smallest |GWP − mean|; for equal distance the lower GWP wins (deterministic).
- Mean over **all strength classes** of a material (e.g. C20/25, C25/30, C30/37 together).
- **wd_rib**: the mean section is optimized for both `t3` cases; per span, criterion and optimum the **worse** one is kept: higher GWP if optimized for GWP, higher section (`h_rib + t2 + t3`) if optimized for height. If one of the two cases is infeasible, the result counts as infeasible.
- **KBOB**: no mean section, because KBOB has one product per material (min = max = mean, it would be a duplicate).
- Several `criteria` / `optima` in one run: still one mean section, optimized once per criterion and optimum (like every other section).

### 4.3 Example (database_261009, EPD)
| material | products | min / max GWP | mean GWP | chosen product |
|---|---|---|---|---|
| concrete | 33 | 63.5 / 121.0 | 84.9 | 36 (C30/37) |
| rebar B500B | 11 | 303.0 / 821.0 | 548.0 | 108 |
| timber (glulam + solid, pooled) | 28 | 105.7 / 442.1 | 251.2 | 212 (glulam GL24h, 246.1) |
| board (plywood) | 10 | 170.3 / 556.0 | 296.7 | 216 |

GWP values in kgCO₂eq/t as in the database. Test batch (5 lengths 4–12 m, `ENV`, `GWP`): one mean section per run, 5 rows each.

| run | mean section | result |
|---|---|---|
| rc_rec, massiv | concrete 36 + rebar 108 | feasible for all spans |
| rc_rib, Schuettung | concrete 36 + rebar 108 | feasible for all spans |
| wd_rec, Vollholz | timber 212 | feasible 4–6 m; 8–12 m infeasible (h > 28 cm) |
| wd_rib, Hohlkasten | timber 212 + board 216 | feasible for all spans; worse case was `t3 = 0.04 m` everywhere |
| rc_rec, KBOB | – | no mean section (intended) |

### 4.4 Implementation walk-through
**Template (`261009_Template_Examples.py`)**
1. `DEFAULTS["mean_gwp"] = True` switches the mean section on for every run; a run can set `"mean_gwp": False`.
2. `check_run` checks that `mean_gwp` is `True` / `False`; `effective_key` includes it (only relevant for EPD), so two runs that only differ in `mean_gwp` for KBOB count as identical.
3. The optimization loop passes `mean_gwp=run["mean_gwp"]` to `opt_and_plot.plot_dataset`.
4. After the optimization, `keep_worse_t3(results)` reduces the wd_rib mean section to the worse `t3` case (all other entries are unchanged). Then `member_row` builds the rows; `mean_section` is written into the material selection block.

**`opt_and_plot.py`**
1. `get_products_by_gwp(cursor, material, mech_prop, basetype)`: one SQL query for all products of a material (density and MECH_PROP given, `source_filter` for EPD / KBOB), sorted by GWP. Shared by:
   - `get_low_high_prod_ids(...)`: lowest and highest GWP product (unchanged behaviour, used for rebar and board),
   - `get_mean_prod_id(cursor, materials, mech_prop, basetype)`: mean GWP of all products (`materials` can be one pattern or a list, which is pooled), returns the closest product.
2. `plot_dataset(..., mean_gwp=False)`: default off, so all other scripts behave as before.
   - First all products of all `mat_names` are collected as `(prod_id, is_mean=False)`.
   - If `mean_gwp` and EPD: one more entry `(get_mean_prod_id(all mat_names), is_mean=True)`.
   - The loop builds each section exactly like before; for `is_mean = True`, rebar rsp. board come from `get_mean_prod_id` instead of `get_low_high_prod_ids`.
   - Each section in `to_plot` carries `is_mean`; it is passed on in `results` as `"mean_section"`.
3. Plots and the raw `Members_*.xlsx` from `plot_dataset` contain the mean section with **both** `t3` cases; the worse-case selection only applies to the batch Excel of the template.

### 4.5 Open points / to discuss
- Mean over all strength classes: the mean concrete is a C30/37. A mean per strength class would be a small change.
- wd_rec: the mean timber is also optimized in the normal loop (same product, no secondary material) → the mean section is a marked duplicate there.
- History: the database has a column `MIN_MAX` (min / max per material and strength class). In 1D it was used only briefly (5 Aug 2026, `889c489`, removed again in `3ed9a9d`); today only `plot_datasets_2D.py` uses it. The 1D template loops over all products.

## 5. Output (`Workflow/Results/`)
- One `<YYMMDD_HHMM>_batch_<group>.xlsx` per material group (see above); sheet `runs` holds the settings and status (ok / failed) of the group's runs.
- Raw files per run (written by `plot_dataset`): `Members_{crsec_type}{_simple|_cont|_2span}_{floor}_{basetype}[_runNN].xlsx`.

## 6. How to use
1. Run from inside `Workflow/`: `.venv/bin/python 261009_Template_Examples.py` (databases are opened by relative path).
2. Set `CHECK_ONLY = True` first to see the overview, then set it to `False` and run.

## 7. Good to know
- `alg` only affects concrete sections.
- wd_rib runs twice per product (two `t3` cases); this is intended.
- KBOB has only one rebar (B500B), so it gives fewer datasets than EPD; this is intended.
- wd_rec is limited to a section height of **28 cm** (`available_h` / `h_max` in `struct_optimization.opt_gzt_wd_rqs`, "max. available thickness of solid timber slabs"); longer spans become `feasible = False`. No source is given in the code.
- **rc_rib GWP is wrong for rib spacings `b ≠ 1 m`** (unit error in `RibbedConcrete`), see `SUMMARY_KBOB_EPD.md` §6.1.
- 2D slabs are not covered (`slab_2d_optimization.py`).

## 8. Possible next steps
- Plot script that reads the `_batch_<group>.xlsx` files (group by `plot_label` / `label`).
- Move Part 2 into a module (e.g. `Workflow/batch_runner.py`) so that the template only holds the settings.
- Resume (skip runs that already have results), parallel runs, and fixed seeds so TPE results can be reproduced.
