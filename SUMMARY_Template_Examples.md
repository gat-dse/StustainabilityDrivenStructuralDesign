# Summary: `Workflow/261009_Template_Examples.py` (2026-10-09)

**Repo:** branch `cleanup/archive`, base commit `36ba32b`. The file is new and uncommitted. EPD/KBOB background: `SUMMARY_KBOB_EPD.md`.

## 1. Purpose
A starting point for running 1D examples (concrete and timber, simple beam / continuous / two span). Copy the file, adjust the settings, and switch datasets on or off in the `runs` list.

It combines the best parts of the existing input scripts:

| Taken from | What |
|---|---|
| `260513_simple_span_1d_Concrete.py` | Concrete floor structures `massiv` / `Schuettung` with names, timing, plot labels and axis limits |
| `260730_Anwendung_Timber.py` | Timber floor structures incl. the `h_ins` correction for the box section (Hohlkastendecke, REI60 per Lignum 4.1) |
| `TestAlgorithm.py` | `alg` setting (`"basinhoppin"` or `"TPE"`) |
| `PB_Einfeld.py` / Timber | `basetype = "epd"` / `"kbob"` |

## 2. Structure
1. **SETTINGS:** `lengths`, `idx_vrc = len(lengths) - 1`, `max_iter`, `alg`, `criteria`, `optima`, `database_name`, `basetype`, loads `g2k`/`qk`, `Requirements()`.
2. **FLOOR STRUCTURES:** `bodenaufbau_rc` ("massiv"), `bodenaufbau_rc_rib` ("Schuettung"), `bodenaufbau_wd_solid` ("Vollholz"), `bodenaufbau_wd_rib` ("Hohlkasten"). All have a `name`, so the Excel file names can tell them apart. The Timber script left the names empty.
3. **MATERIALS:** `mat_names_rc`, `mat_names_wd`.
4. **RUNS:** one dict per dataset (`crsec_type`, `mat_names`, `floorstruc`, `system`). Comment lines out to switch them off. Active by default: `rc_rec`, Simple Beam.
5. **OPTIMIZATION:** one loop calls `opt_and_plot.plot_dataset(...)` and always passes `system`, `alg` and `basetype` by name. None of them can fall back to a default by accident, which is how the Concrete script used to run EPD without saying so.
6. **PLOT:** labels, axis limits, grid, `plt.show()`. The cross-section verification plot is included but commented out.

## 3. How to use
- Run from inside `Workflow/` with `.venv/bin/python 261009_Template_Examples.py`. The databases are opened by relative path, and the system `python3` has no numpy.
- Results: `Workflow/Results/Members_{crsec_type}_{system}_{floor}_{basetype}.xlsx`.

## 4. Tested (2026-10-09, on a scratch copy, 2 spans, 5 iterations)
- `rc_rec` + `basetype = "kbob"` → runs, `Members_rc_rec_simple_massiv_kbob.xlsx`.
- `wd_rib` + `basetype = "epd"` → runs, `Members_wd_rib_simple_Hohlkasten_epd.xlsx`.
- These short runs only show that the code runs. The results were not checked.
- Not tested: `rc_rib`, `wd_rec`, `Continuous 1D`, `Two span 1D 1D`, full-length runs.

## 5. Issues to know about

### In the template / affecting it
- **`rc_rib` GWP is wrong for rib spacings `b ≠ 1 m`** (unit error in `RibbedConcrete`). The optimizer favours wide rib spacings. Details and chain of events: `SUMMARY_KBOB_EPD.md`, Section 6.1. Treat `rc_rib` results with care until it is fixed.
- **Verification plot crashes for `wd_rib`:** if you uncomment the `plot_section` loop at the end (l.~139) while a `wd_rib` run is active, `plot_wd_rib_with_dimensions` raises `NameError: name 'a' is not defined`. Details: `SUMMARY_KBOB_EPD.md`, Section 6.2.
- **`alg` only affects concrete sections:** `wd_rec` and `wd_rib` use their own algorithm in `struct_optimization.get_optimized_section`. `Continuous 1D` + `rc_rib` uses `struct_optimization_RCrib_cont.py`.
- **`wd_rib` runs twice per product**, once per top-plank thickness `t3` in `T_KANDIDATEN_WDRIB = [0.027, 0.04]` (`struct_optimization.py` l.1114). This is intended, and it doubles the runtime.
- **KBOB has only one rebar (B500B)**, so a KBOB concrete run has half as many lines as an EPD run. Intended, not a bug.
- **`idx_vrc` must be smaller than `len(lengths)`.** The template sets `len(lengths) - 1`. `-1` means a random length.

### Found in the other input scripts while building the template
- **`260730_Anwendung_Timber.py`:** `idx_vrc = 4` with `lengths = [4, 6, 8, 10]` (indices 0–3). No length is ever picked for verification, and no error is raised. Duplicated `import opt_and_plot` on l.4 (as text in the comment).
- **`260513_simple_span_1d_Concrete.py`:** had no `basetype` and silently used the default `"epd"`. Fixed: `basetype` added and passed to all 8 calls.
- **`TestAlgorithm.py` / `PB_Einfeld.py`:** the verification `plot_section` loop is inside a `"""…"""` block, so it doesn't run. If enabled with `wd_rib`, it hits the `NameError` above.
- **2D slabs are not covered by the template.** `slab_2d_optimization.py` uses `plot_datasets_2D.plot_dataset` with other arguments (`length_x`, `length_y`, `support`) and only supports `rc_rec`. It needs at least two slab sizes, and `MIN_MAX = 1` rows for the selected data basis. See `SUMMARY_KBOB_EPD.md`, Section 5.
