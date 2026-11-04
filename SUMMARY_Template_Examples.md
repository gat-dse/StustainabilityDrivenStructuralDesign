# Template_Examples – Summary

## 1. Purpose
`Workflow/261030_Template_Examples_1D.py` runs a batch of 1D optimizations (rc_rec, rc_rib, wd_rec, wd_rib on Simple Beam / Continuous 1D / Two span 1D 1D) and writes the results into **one Excel file** with one sheet per run. Plotting happens later, in a separate step, from these files.

Copy the file and only edit Part 1.

## 2. What you set (Part 1)
- `CHECK_ONLY`: `True` → only check the runs and print the overview, no optimization.
- `DEFAULTS`: values every run uses unless it sets its own: `system`, `basetype` (epd / kbob), `alg`, `max_iter`, `lengths`, `criteria`, `optima`, `g2k`, `qk`, `use` (Nutzung, label only), `min_max_only` (`True`: only main products with `MIN_MAX = 1`, `False`: all; EPD only, rebar, boards and mean sections are not affected), `mean_gwp` (mean section on/off, see §4).
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
1. Pick the database products of the chosen materials and `basetype`; with `min_max_only = True` and `basetype = "epd"` only those with `MIN_MAX = 1`.
2. Build one initial cross-section per product. For rc this is done twice, with the lowest-GWP and highest-GWP rebar; for wd_rib it is done with the lowest- and highest-GWP board.
3. With `mean_gwp = True` and `basetype = "epd"`: add **mean sections** (see §4).
4. For every section × criterion × optimum × length: build the static system and a `Member1D` with the loads, then optimize the section (`struct_optimization`, or `struct_optimization_RCrib_cont` for rc_rib on Continuous 1D). wd_rib is optimized once per fixed `t3` case (0.027 m and 0.04 m).
5. Every optimized member is verified with `struct_optimization.failed_checks`, whatever criterion it was optimized for: ULS, SLS1, FIRE (not wd_rib) and the rib width for rc_rib, SLS2 for wood only. `feasible = True` means all of them are fulfilled; otherwise `feasible = False` and `failed_checks` names the failed ones (`no section` if the optimizer returned none, e.g. the span is too long for wd_rec). These members stay in the batch Excel, but not in the plots and `Members_*.xlsx`.

An unexpected error inside a run is printed, the run is marked `failed`, and the batch continues with the next run.

**Step 5 – Collect and save the results** (`member_row`, `SECTION_COLUMNS`)
Each optimized member becomes one row. All results go into **one Excel** `<YYMMDD_HHMM>_batch_1D.xlsx`, with **one sheet per run** (`00`, `01`, ..., failed runs have no sheet), followed by the sheet `runs`.

Columns of a sheet, in blocks (order of the supervisor's table; units in brackets; forces in kN, loads in kN/m², CO₂ per m² of floor). Header colors: **green** = configuration / selected data, **yellow** = results, **red** = key results `MEd_n`, `MEd_p`, `VEd`, `co2_struct` (`KEY_COLUMNS`, overrides the block color).

| block | color | all types | rc_rec | rc_rib | wd_rec | wd_rib |
|---|---|---|---|---|---|---|
| identification | – | `member_id`, `criterion`, `optimum` | | | | |
| data source | green | `basetype`, `use` | | | | |
| design configuration | green | `plot_label`, `label`, `run_nr`, `dataset`, `crsec_type`, `system`, `g2k`, `qk`, `feasible`, `failed_checks` | `alg` | `alg` | | |
| geometry | – | `l_tot`, `h_struct`, `b` | | `b_w`, `h_f` | | `b_w`, `h_rib`, `t2`, `t3` (`h_struct` = h_rib + t2 + t3, `b` = rib spacing) |
| material selection | green | name + `_prod_id` + `_GWP` | `concrete`, `rebar` | `concrete`, `rebar` | `timber` | `timber`, `board` |
| structural results | yellow | `MEd_n`, `MEd_p`, `VEd` | `rebar_content [kg/m3]` | `rebar_content` | | |
| co2 structure | yellow | `co2_struct` | `co2_concrete`, `co2_rebar` | `co2_concrete`, `co2_rebar` | | `co2_rib`, `co2_board` |
| floor build-up | – | `floor`, `h_floor`, `g_floor`, `co2_floor`, `co2_floor_per_year` | | | | |
| final indicators | yellow | `h_tot`, `g_struct`, `g_tot` (dead loads), `co2_tot` | | | | |

`member_id` = `<run in the batch>-<member in the run>`, both counted from 0: the first run gives `00-000`, `00-001`, …, the second `01-000`, …. Runs are counted from 0 everywhere (`nr` in sheet `runs`, `run_nr`, sheet name, error messages). `use` (Nutzung, default `"Wohnen"`) is only a label; `qk` has to fit it.
Spans with `no section` only have identification, settings, span and materials; a section that fails a verification keeps all result columns.
A new cross-section type needs one function in `SECTION_COLUMNS`.
Mean sections are marked with `mean_section = True` (block material selection); their `_prod_id` is `mean_of_<n>` (n = number of averaged products).

## 4. Mean sections (`mean_gwp`)

Toggle: `DEFAULTS["mean_gwp"]`, a run can override it. EPD only; ignored for KBOB (one product per material). Mean sections are **added** to the sections of the single products.

### 4.1 Rules
- For each material of a run, the products are grouped by strength class. Each group gives one **mean material**: arithmetic mean of GWP and arithmetic mean of density (needed because CO2 = volume × GWP × density). Strength values come from the strength class as usual. UBP and Graue Energie are not averaged (NaN).
- The mean material is not a real product (`prod_id` = `mean_of_<n>`).
- GL classes without `h` or `c` count as `c` (`GL24` belongs to `GL24c`, conservative), same rule for the single products and the mean materials, in 1D and 2D.
- Every mean of the main material is combined with the mean of the secondary material:

| run | mean sections | secondary material |
|---|---|---|
| rc_rec, rc_rib | 3 (C20/25, C25/30, C30/37) | mean of all B500B rebars (11 products) |
| wd_rec | 9 (8 glulam classes + C24 solid) | – |
| wd_rib | 9, as wd_rec | mean of the C24 boards (8 products), the strength every board is calculated with |

- **wd_rib**: each mean section is optimized for both `t3` cases (0.027 m, 0.04 m) and **both are kept** as separate rows, like the sections of the single products (column `t3`). `t3` is not averaged or selected, because only these two thicknesses are real board thicknesses.
- Classes with one product (e.g. `GL32h`) give a mean equal to that product, so the mean section repeats its product section.

### 4.2 Implementation
- `opt_and_plot.get_mean_materials`: builds the mean materials of one material. `apply_mean_material`: overwrites the values of a material object. `get_secondary_products`: rebar rsp. board for one main material.
- `plot_dataset(..., mean_gwp=False, min_max_only=False)`: default off, other scripts behave as before. The 2D `plot_dataset` keeps its own default `min_max_only=True`.

## 5. Output (`Workflow/Results/`)
- One `<YYMMDD_HHMM>_batch_1D.xlsx` (see above); sheet `runs` holds the settings and status (ok / failed) of all runs.
- Raw files per run (written by `plot_dataset`): `Members_{crsec_type}{_simple|_cont|_2span}_{floor}_{basetype}[_runNN].xlsx`.

## 6. How to use
1. Run from inside `Workflow/`: `../.venv/bin/python 261030_Template_Examples_1D.py` (or `_2D.py`) (databases are opened by relative path).
2. Set `CHECK_ONLY = True` first to see the overview, then set it to `False` and run.

## 7. Good to know
- `alg` only affects concrete sections.
- wd_rib runs twice per product (two `t3` cases); this is intended.
- KBOB has only one rebar (B500B), so it gives fewer datasets than EPD; this is intended.
- wd_rec is limited to a section height of **28 cm** (`available_h` / `h_max` in `struct_optimization.opt_gzt_wd_rqs`, "max. available thickness of solid timber slabs"); longer spans become `feasible = False`. No source is given in the code.
- **rc_rib GWP is wrong for rib spacings `b ≠ 1 m`** (unit error in `RibbedConcrete`), see `SUMMARY_KBOB_EPD.md` §6.1.
- 2D slabs have their own template, see §9.

## 8. Possible next steps
- Plot script that reads the `_batch_1D.xlsx` / `_batch_2D.xlsx` files (group by `plot_label` / `label`).
- Move Part 2 into a module (e.g. `Workflow/batch_runner.py`) so that the template only holds the settings.
- Resume (skip runs that already have results), parallel runs, and fixed seeds so TPE results can be reproduced.

## 9. 2D template (`Workflow/261030_Template_Examples_2D.py`)
Same structure as the 1D template (Part 1 settings, checks before optimizing, one Excel `<YYMMDD_HHMM>_batch_2D.xlsx` with one sheet per run and the sheet `runs`, runs counted from 0). Differences to 1D:

- **Scope**: square `rc_rec` slabs only (lx = ly). `lengths` are slab spans; the check rejects spans missing in `260625_slab_properties.db`.
- **Supports** (`support` instead of `system`): `LL-frei`, `LL-eingespannt`, `PL-eingespannt` (no 4 m; no feasible section at 8 and 10 m with the tested material). `drop_beam` is not allowed.
- **Products**: all EPD products, same as 1D (`min_max_only=False`). `slab_2d_optimization.py` keeps the old `MIN_MAX = 1` selection.
- **Mean sections**: same rules as §4, 3 per span (C20/25, C25/30, C30/37 with mean B500B).
- **`alg`**: `TPE` (default) or `basinhoppin`. `slab_2d_optimization.py` stays on `basinhoppin`.
- **TPE** (`struct_optimization_2D.opt_rc_rec_tpe`): 5 variables: `h` in 1 cm steps and the 4 layer diameters from `BEWEHRUNG_D`; spacing stays fixed at 0.15 m. Start: `h = L/25`.
- **`max_iter`**: default 800 (1D: 50). With 5 variables TPE converges slower: 50 iterations gave up to 75 % higher GWP than 1600, 800 stayed within about 3 %. About 2 s per optimization.
- **Feasibility**: same check as 1D, for TPE and basinhoppin.
- **Columns**: `support` instead of `system`; geometry also holds the diameters and spacings of all 4 layers.
- **Raw files**: `Members_2D_<support>_<basetype>[_runNN].xlsx`.
