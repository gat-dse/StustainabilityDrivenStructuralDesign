# Summary: EPD/KBOB switch + UBP & Graue Energie (2026-10-09)

**Repo:** branch `cleanup/archive`, base commit `36ba32b`. Changes are uncommitted. Code paths are under `Workflow/`. Line numbers refer to the working tree on 2026-10-09.

Replaces `HANDOFF_KBOB.md` (plan, now implemented, deleted) and includes the open problems from `HANDOFF_OP.md` (Section 6).

**Goals**
1. Choose the data basis per run with `basetype = "epd"` (product EPDs) or `"kbob"` (generic KBOB v9.0 values).
2. Read UBP and Graue Energie from the database and compute them per section, the same way as GWP. They are **info values only** and do not affect the optimization.

**Marking convention:** every change has a marker comment `### KBOB: …` directly above it. Find them all with `grep -rn "### KBOB" Workflow Database`. They are still in the code (72 markers in 14 files). Remove them after reviewing.

---

## 1. Data basis

Source: `Database/260811_Datenbankdefinition.xlsx`, sheet `products` → `Database/Convert_Excel_to_DB.py` → `database_261009.db` (copy it to `Workflow/` after each conversion).

- **KBOB vs. EPD:** a row is **KBOB** if `"KBOB ID-Nr." IS NOT NULL` (57 rows). Every other row is **EPD**.
  - Only KBOB rows have a `KBOB ID-Nr.` in the Excel; it is empty for all other rows, and `to_sql` writes NULL. Checked 2026-10-11: exactly the 57 `SOURCE = 'KBOB v9.0'` rows have one.
  - Changed on 2026-10-11 from `EPD_ID IS NULL AND SOURCE = 'KBOB v9.0'`. The new condition doesn't depend on the version string and can't become NULL when `SOURCE` is empty. The 11 `Betonsortenrechner` rows (PRO_ID 12–22) have no KBOB ID, so they stay out of KBOB mode.
- **Filters** (`source_filter(basetype)`):
  - `epd`: `NOT KBOB AND ValidEPD = 1 AND Man_Ausschluss = 1`. This returns exactly the same products as before the change.
  - `kbob`: `KBOB AND Man_Ausschluss = 1 AND CAST(Total_GWP AS REAL) > 0`. The last condition drops the all-zero row 01.002.09.
- **Units:** `Total_GWP` [kg CO2-eq/t], `total_UBP` [UBP/t], `Graue_Energie` [kWh oil-eq/t]. All three are divided by 1e3 in the code to get per kg. Checked against the KBOB source (`Ökobilanzdaten_im_Baubereich_V9.0.xlsx`): e.g. Hochbaubeton 0.101 kg CO2-eq / 153 UBP / 0.175 kWh per kg.
- **UBP/GE exist only for KBOB rows.** EPD rows are empty, so EPD mode reports NaN (by decision). NaN appears as an empty cell in the Excel output.
- **KBOB products available now** (`Man_Ausschluss = 1`, GWP > 0):

  | Material | MECH_PROP | Rows |
  |---|---|---|
  | ready_mixed_concrete | C20/25 / C25/30 / C30/37 | 15 / 8 / 12 |
  | Steel_reinforcing_bar | B500B | **1** (PRO_ID 98) |
  | Glue_laminated_timber | GL24h | 3 |
  | Solid_structural_timber / Structural_timber | C24 | 1 / 1 |
  | 3_and_5_plywood | OSB/3, OSB/4 | 2 |

- **`MIN_MAX` (only used by the 2D slab workflow):** marks the lowest- and highest-GWP concrete per strength class. It applies to both data bases. Set on 2026-10-09 in the Excel:
  - EPD: 23, 34 (C20/25) · 33, 35 (C25/30) · 31, 44 (C30/37)
  - KBOB: 94, 63 (C20/25) · 95, 64 (C25/30) · 96, 65 (C30/37)
  - Example: The generic "Hochbaubeton KBOB" (PRO_ID 97, C25/30) is neither lowest nor highest, so it is not marked.

## 2. Code changes

### `Workflow/opt_and_plot.py` (1D workflow)
- **`source_filter(basetype)`** + `KBOB_CONDITION` at module level (l.18–29).
- **`get_low_high_prod_ids(cursor, material, mech_prop, basetype)`** (l.33): replaces the three copied min/max queries (rebar for rc_rec, rebar for rc_rib, plywood for wd_rib). It returns the **unique** product IDs with the lowest and highest GWP. With one KBOB rebar (min = max) it returns a single ID, and the caller builds one section per ID. Before, `result[1]` would have raised an IndexError.
- **`plot_dataset(..., basetype="epd")`**: filter in the main product query and in all low/high queries. The default keeps old calls working.
- **`basetype` in the legend and in the Excel name:** `Members_{crsec_type}{system}{floor}_{basetype}.xlsx`, so EPD and KBOB runs don't overwrite each other.
- **`plot_section_dataset(..., basetype="epd")`** (l.706): same filter.
- **Legend in `plot_section`:** UBP and GE lines next to GWP.

### `Workflow/plot_datasets_2D.py` (2D slab workflow), minimal changes only
- Local copy of `source_filter` (same conditions as in `opt_and_plot.py`, nothing imported).
- `plot_dataset(..., basetype="epd")`. The main query and both rebar min/max queries use `source_filter(basetype)` instead of `ValidEPD = 1 AND Man_Ausschluss = 1`. The original query structure is unchanged, including `MIN_MAX = 1` and `section_00`/`section_01`.
- `prod_id_high = result[-1]` instead of `result[1]` (2×): KBOB has only one rebar, so the query returns one row. For EPD (2 rows) it is the same product as before.
- Excel name: `Members_2D_{support}_{basetype}.xlsx`.

### `Workflow/struct_analysis.py`
- **`per_kg(v)`** helper: `float(v)/1e3`, or NaN if empty.
- **Material classes** `Wood`, `ReadyMixedConcrete`, `SteelReinforcingBar`: also read `total_UBP` and `Graue_Energie` → `self.UBP`, `self.graue_energie` [per kg].
- **Section classes**: new `ubp*` / `graue_energie*` attributes next to each `co2` line, with the same mass expression: `RectangularWood`, `RectangularConcrete`, `FlatSlab2D`, `RibbedConcrete` (incl. the known unit error, see 6.1), `RibWood`.
- The optimizers only read `section.co2`, so results don't change.

### Input scripts: `basetype = "epd"` next to `database_name`, passed to every `plot_dataset(...)` call
- `260513_simple_span_1d_Concrete.py` (8 calls, incl. the commented-out ones). Before, it had no `basetype` and silently used the default `"epd"`.
- `260730_Anwendung_Timber.py`, `PB_Einfeld.py`, `TestAlgorithm.py`, `slab_2d_optimization.py`.
- New template `261009_Template_Examples.py` (see `SUMMARY_Template_Examples.md`).

### Database name `database_261009.db`
- `Database/Convert_Excel_to_DB.py`, `database_check.py`, and all input scripts. (`test_the_database.py` and `plot_products_NeueDB251030.py` moved to `archive/260909_Database_old/` on 2026-10-10.)

## 3. Verification done (2026-10-09)
- DB: 57 KBOB rows. `total_UBP` and `Graue_Energie` are present.
- **Spot check UBP** (rc_rec, KBOB concrete 62 + KBOB rebar 98): `ubp_concrete / co2_concrete` = 1661.9 = 174000 / 104.7 ✓; `ubp_rebar / co2_rebar` = 2025.5 = 1590000 / 785 ✓. EPD concrete 31: UBP/GE = NaN ✓.
- **1D template, quick runs** (2 spans, 5 iterations): rc_rec + KBOB → `Members_rc_rec_simple_massiv_kbob.xlsx`; wd_rib + EPD → `Members_wd_rib_simple_Hohlkasten_epd.xlsx`.
- **2D slab, quick runs** (`max_iter = 2`, 3×3 and 4×4 m, both supports):
  - EPD: 48 optimizations, concretes 23/31/33/34/35/44, rebars 120/123.
  - KBOB: 48 optimizations, concretes 63/64/65/94/95/96, rebar 98.
- **Not done:** a full EPD run compared with results from before the change (GWP/h should be identical). Full-length runs with KBOB.

## 4. How to use
1. After changing the Excel: run `Convert_Excel_to_DB.py` from inside `Database/`, then copy `database_261009.db` to `Workflow/`.
2. In the input script, set `basetype = "epd"` or `"kbob"`.
3. Run from inside `Workflow/` with `.venv/bin/python`. The databases (`database_261009.db`, `260625_slab_properties.db`) are opened by relative path.

## 5. Issues found during the implementation
- **Only one KBOB rebar (B500B).** In 1D, `get_low_high_prod_ids` returns one ID, so a KBOB run has half as many lines as an EPD run. In 2D, `section_00` and `section_01` get the same rebar, so every KBOB line is computed twice and plotted twice. Both resolve themselves once more KBOB rebars are added to the data.
- **2D: `MIN_MAX = 1` also applies to KBOB.** Before the Excel update, all KBOB rows had `MIN_MAX = 0`, so a KBOB run found no concrete. It **failed silently**: no error, nothing optimized, no Excel file, but "Excel … erstellt" was still printed. Check `MIN_MAX` whenever KBOB rows are added.
- **2D needs at least two slab sizes.** With one size, the envelope polygon (shapely) raises `ValueError: A linearring requires at least 4 coordinates`.
- **2D `Slab` class** opens `260625_slab_properties.db` by relative path → run from `Workflow/`.
- **The duplicated rebar queries in plot_datasets_2D.py**:
  In plot_dataset, the branches rc_rec (l.~90) and rc_rib (l.~140) each contain the same rebar min/max query that we merged into get_low_high_prod_ids in the 1D file. The 2D copy was deliberately left unchanged at the time. Only source_filter(basetype) was added, and result[1] was changed to result[-1]. That leaves these problems:
  1. cursor.execute(inquiry) twice in a row in rc_rib. This is harmless: the second call just runs the same query again, and only that result is read. It wastes a little time and is a copy-paste leftover.
  2. low / high labels can be swapped. The IN (MIN, MAX) query returns rows in PRO_ID order, not GWP order. With the current EPD data:
   - result[0] = PRO_ID 120 (GWP 821, the highest), and it goes into rebar_low_em.
   - result[-1] = PRO_ID 123 (GWP 303, the lowest), and it goes into rebar_high_em.
   - Both lines are computed anyway, so the plots are correct, but the variable names are wrong. It's the same issue as the old 1D code.
  3. KBOB computes everything twice. There is only one KBOB rebar, so result[0] and result[-1] are the same product. section_00 and section_01 are identical, and every optimization runs twice and gets plotted twice.
    4. Ties. If two rebars share the min or max GWP, the query returns more than 2 rows, and result[-1] is not guaranteed to be the max.
  5. The same query runs once per concrete product, for example 6 times for 6 concretes, always with the same result. This is not a bug, just unnecessary work.
  The fix is to copy get_low_high_prod_ids into plot_datasets_2D.py (like source_filter), or import it, and loop over the returned IDs the same way as in 1D. That fixes 1–4.

  One thing to check before changing rc_rib: unlike in 1D, section_00 and section_01 there don't only differ by rebar. They also have different starting parameters (…, 0.018, 2, … vs. …, 0.018, 3, …). A shared loop would give both the same starting values, so you'd need to decide whether that difference is intended. According to the summary, the 2D workflow currently only runs rc_rec anyway.
- **Floor structure BODEN AUFBAU** (`MatLayer` / `floor_struc_prop`) has no UBP/GE columns yet, so `GWP_tot` has no UBP/GE counterpart. Out of scope.

## 6. Open problems (from `HANDOFF_OP.md`, not fixed)

### 6.1 Unit error in the rc_rib GWP (`struct_analysis.py`, `RibbedConcrete`)
UBP/GE in `RibbedConcrete` use exactly the same formula as GWP on purpose, so all three can be fixed together in one place.

**Chain of events** (`b` = rib spacing, axis to axis):
1. **l.739 / 748** `a_brutt = b·h_f + b_w·(h − h_f)` → concrete of one rib strip of width `b`, per m' of span [m²]. *Correct.*
2. **l.855–858** `as_p`, `as_n` per m width [m²/m] (`mu_unsigned` with `b = 1`, l.927); `as_PB_p` rib bars of one rib [m²] (l.988). *Correct.*
3. **l.880–883** `as_Platte = (as_p + as_n)·b·2`, `as_Rippe_bg`, `as_Rippe_x` → `as_stat_2` = rebar volume of the strip per m' [m³/m'], same basis as `a_brutt`. *Correct* (comment says `[m3]`).
4. **l.888** `a_s_tot = as_stat_2·(1+js) / b` → already converted to per m² of floor. **← start of the problem.**
5. **l.891** `Bew_Gehalt = a_s_tot·ρ_s / (h_w·b_w + h_f·b)` → divides by `b` once too often. **Error A.** Correct: `as_stat_2·(1+js)·ρ_s / a_brutt`.
6. **l.893** `co2_rebar = a_s_tot·GWP·ρ_s / b` → divides by `b` a second time. **Error B.** Correct: `as_stat_2·(1+js)·GWP·ρ_s / b`.
7. **l.894** `co2_concrete = (a_brutt − a_s_tot)·GWP·ρ_c / b` → per-m² steel subtracted from per-strip concrete. **Error C** (small). Correct: `(a_brutt − as_stat_2·(1+js))·GWP·ρ_c / b`.
8. **l.896** `co2` → wrong for every `b ≠ 1`.
9. **l.899–904** `ubp_*`, `graue_energie_*` → same error.
10. **l.905** `cost` → same unit mix, also not divided by `b`. Harmless for now because `cost = 0`.
11. **Where the wrong value goes:**
    - `struct_optimization.py` l.621 `bb = (0.4, 3.8)`, l.692 `suggest_float("b", …)`, l.776 → `b` is an optimization variable.
    - `struct_optimization.py` l.904–932 and `struct_optimization_RCrib_cont.py` l.231–261 minimize `section.co2` → **the optimizer is steered by the wrong GWP.**
    - `Member1D.co2` (l.1622), GWP plots (`opt_and_plot.py` l.257/266), legend (l.494), Excel export (incl. `Bew_Gehalt`).

**Numerical check** (EPD concrete + B500B, b_w = 0.30, h = 0.50, h_f = 0.20, 4Ø20):

| b [m] | co2 code [kg/m²] | co2 correct | Bew_Gehalt code [kg/m³] | correct |
|---|---|---|---|---|
| 0.5 | 116.1 | 93.8 | 269.9 | 134.9 |
| 1.0 | 69.8 | 69.8 | 121.0 | 121.0 |
| 2.0 | 51.9 | 57.8 | 55.1 | 110.2 |
| 3.0 | 47.3 | 55.5 | 40.9 | 122.8 |

→ For `b > 1` the rebar GWP is underestimated by the factor `b`, so the GWP-optimized rc_rib tends towards wide rib spacings.

**Proposed fix:** compute `m_rebar` and `m_concrete` [kg/m²] once, then derive `co2_*`, `ubp_*`, `graue_energie_*` and `Bew_Gehalt` from them. This changes rc_rib results, so re-run and compare afterwards. Other section classes are fine: `RectangularConcrete`, `FlatSlab2D`, `RectangularWood` use b = 1 m; `RibWood` is per m².

### 6.2 `NameError` in `plot_wd_rib_with_dimensions` (`opt_and_plot.py`)
Not caused by the KBOB changes; it already exists at `36ba32b`.

**Chain of events:**
1. **Entry points** calling `opt_and_plot.plot_section(section)`: verification loops in `PB_Einfeld.py` l.109 and `TestAlgorithm.py` l.119 (both inside `"""…"""`, not executed), `261009_Template_Examples.py` l.139 (commented out), and `plot_section_dataset` l.773.
2. **l.454** `plot_section` dispatches on `section_type`.
3. **l.499–500** branch `"wd_rib"` → `plot_wd_rib_with_dimensions(section.bw, section.h, section.b, section.t2, section.t3, …)`.
4. **l.589** the function has no parameter or local variable `a`.
5. **l.591** `plt.subplots()` → an empty figure is opened before the crash.
6. **l.598** `rect_rib1 = patches.Rectangle((offset+a/2, …))` → **`NameError: name 'a' is not defined`** (reproduced). l.600 (`3*a/2`) would fail the same way.
7. **Consequence:** the script stops; later datasets/plots are not produced. The optimization results are not affected.
8. **Cosmetic, l.611–612:** both labels show `bw`; `b`, `t2`, `t3` are not shown.

**Proposed fix:** replace `a` with `b` and centre the ribs like the concrete version (l.557/559): `offset + b/2 - bw/2` and `offset + 3*b/2 - bw/2`. Then check the labels. **Check:** build a `RibWood` section and call `opt_and_plot.plot_section(section)`.
