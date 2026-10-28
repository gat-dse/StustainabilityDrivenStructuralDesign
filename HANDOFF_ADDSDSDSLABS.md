# Handoff: add the SDSD_Bieg slab types to this repo (2026-10-04)

**Source repo (S):** `/Users/luizlindzus/SDSD_Bieg` (commit `6f4fd22`, "Final Version")
**Target repo (T):** `/Users/luizlindzus/StustainabilityDrivenStructuralDesign` (commit `36ba32b`; all target paths are under `Workflow/`)

Line numbers below refer to those two commits. Inserting code shifts the target line numbers, so **work from the bottom of each file upwards**. Alternatively, use the named anchors (class/method names), which do not move.

Slab types that exist in S but not in T:

| Slab type | `section_type` | S classes | Scope here |
|---|---|---|---|
| Post-tensioned concrete slab (2D) | `pc_rec` | `PrestressingSteel`, `PostTensionedConcrete` | **Section 1A** |
| Timber-concrete composite (1D) | `tcc` | `ConnectorTCC`, `SupStrucTCC`, `TCC` | **Section 1B** |

Everything else that S has and T lacks is listed in **Section 2**.

---

# Section 1: Plan to add the slabs

## 1.0 Shared prerequisites (needed by both PT and TCC)

### 1.0.1 Database: `Workflow/database_261009.db` (better: the Excel definition it is built from)
T's database lacks what the new classes query:

| Needed by | Missing in T | Fix |
|---|---|---|
| `PrestressingSteel` | `material_prop` row `Y1860` (`strength_tens = 1.86e9`, `E_modulus = 1.95e11`) | Add the row. Values are in `S/database/database_260126.db`, table `material_prop`, name `Y1860`. |
| `PrestressingSteel` | T already has 11 `products` rows with `MATERIAL = 'prestressing steel'` (PRO_ID 265–275), but `MECH_PROP` is `1860`/`2160`/empty and `DENSITY` is empty | Set `MECH_PROP = 'Y1860'` and `DENSITY = 7850` on the rows to use. **Do not copy S's products 121–129**: those PRO_IDs are already taken by rebar and timber in T. |
| `ConnectorTCC` | Table `connector_TCC` (`mat_ID, name, d, K_ser, Cost, T_construction`, plus an optional `GWP`) | Copy the whole table from `S/database/database_260126.db` (6 rows: DBS_6…DBS_12, kerve_20, kerve_30). |
| TCC/PT time model | `products.T_construction` column | Not added. Instead, the material classes default `construction_time = 0.0` (see 1.0.3). |

The permanent fix is to add these to the Excel definition and rebuild with `Database/Convert_Excel_to_DB.py`. The Excel is `Database/260811_Datenbankdefinition.xlsx`. For a quick, local-only patch:
```sql
-- sqlite3 Workflow/database_261009.db
ATTACH '/Users/luizlindzus/SDSD_Bieg/database/database_260126.db' AS s;
CREATE TABLE connector_TCC AS SELECT * FROM s.connector_TCC;
INSERT INTO material_prop (name, strength_tens, E_modulus)
       SELECT name, strength_tens, E_modulus FROM s.material_prop WHERE name = 'Y1860';
UPDATE products SET MECH_PROP = 'Y1860', DENSITY = 7850
       WHERE MATERIAL = 'prestressing steel' AND (MECH_PROP = '1860' OR MECH_PROP = '' OR MECH_PROP IS NULL);
DETACH s;
```

Two data differences to be aware of:
- **Concrete creep coefficient:** T has `creep_coef = 2.0` for C25/30 and C30/37; S has `phi = 2.5`. `TCC.calc_gamma` interpolates around 2.5 (`phi_diff = phi - 2.5`), so TCC results will differ from S's thesis results.
- **Burn rate:** T stores `burn_rate` for C24 and GL24h with the same values as S (0.0008 and 0.0007).

### 1.0.2 `Workflow/struct_analysis.py`: imports, constant, helper
| # | Copy from S | To T | Notes |
|---|---|---|---|
| a | — | after `T:Workflow/struct_analysis.py:32` (`import math`) | Add `import copy` and `from scipy.optimize import root_scalar, least_squares`. TCC fire uses `copy` and `root_scalar`; PT uses `least_squares`. Do **not** copy `from core import paths` / `from pathlib import Path`. |
| b | `S:core/struct_analysis.py:45-55` (`concrete_member_is_uncracked`) | after the imports in T | Only needed if PT Member2D vibration/punching (1A.6) is ported. Harmless otherwise. |
| c | `S:core/struct_analysis.py:57-59` (`g = 10.0`) | after the imports in T | Used for `specific_weight = density * g`. |

### 1.0.3 `Workflow/struct_analysis.py`: make T's material classes provide what PT/TCC read
PT and TCC read `.phi`, `.specific_weight` and `.construction_time` from material objects. T's classes call these `creep_coef` and `weight`, or don't have them at all. Add **aliases**, so no existing code changes:

| T location | Add after the line |
|---|---|
| `Wood.__init__`, after `T:61` (`self.cost2 = 0`) | `self.phi = self.creep_coef`<br>`self.specific_weight = self.density * g`<br>`self.construction_time = 0.0` |
| `ReadyMixedConcrete.__init__`, after `T:110` (`self.cost2 = 0`) | `self.phi = self.creep_coef`<br>`self.specific_weight = self.density * g`<br>`self.construction_time = 0.0`<br>`self.construction_time_scaffold = 0.0` |
| `SteelReinforcingBar.__init__`, after `T:145` (`self.cost = 0`) | `self.specific_weight = self.density * g`<br>`self.construction_time = 0.0` |

T deliberately sets all `cost` values to 0 and `cost2 = 0`; S uses DB costs and 75 CHF/m² formwork. Leave T's choice; the copied classes then report `cost = 0` as well.

### 1.0.4 `Workflow/struct_analysis.py`: new material classes
| # | Copy from S | To T | Changes after pasting |
|---|---|---|---|
| a | `S:core/struct_analysis.py:181-211` (`class PrestressingSteel`) | after `SteelReinforcingBar` (before `T:153`, `#DEFINITIONS OF GEOMETRIC CLASSES…`) | 1) `sqlite3.connect(paths.db_path(database))` → `sqlite3.connect(database)`. 2) In both product SELECTs, remove `, T_construction`, and change the unpack to `self.prod_id, density, GWP, cost = result[0]`, then add `construction_time = 0.0`. |
| b | `S:core/struct_analysis.py:214-240` (`class ConnectorTCC`) | directly after (a) | `paths.db_path(database)` → `database`. Keep the `T_construction` query: it reads the `connector_TCC` table, which has that column. |

---

## 1A Post-tensioned concrete slab (`pc_rec`)

`PostTensionedConcrete` in S subclasses S's `RectangularConcrete`. In T, subclass T's **`RectangularConcrete`** (`T:270`), not `FlatSlab2D`. Reason: T's `RectangularConcrete.calc_d()` returns `(d, ds)` like S's, while `FlatSlab2D.calc_d()` returns 4 values and would break PT's `set_minimalReinforcement`. The constructor argument order (`b, h, di_xu, s_xu, di_xo, s_xo, di_yu, s_yu, di_yo, s_yo, di_bw, s_bw, n_bw, phi, c_nom, xi, jnt_srch`) is identical in S and T.

### 1A.1 Copy the class
| Copy from S | To T |
|---|---|
| `S:core/struct_analysis.py:631-1086` (`# ......` separator + `class PostTensionedConcrete` up to and including its `fire_resistance`) | `T:Workflow/struct_analysis.py`, after `FlatSlab2D` ends (`T:690`), i.e. directly before `T:692 class SupStrucRibbedConcrete` |

### 1A.2 Changes inside the pasted class
| S line (now in T) | Change | Why |
|---|---|---|
| `S:687` `self.g0k = self.calc_weight(volume_concrete, volume_reinforcement, volume_pt_steel)` | Rename the call to `self.calc_weight_pt(...)`, add a method `calc_weight_pt` with the body of `S:core/struct_analysis.py:436-443` (S's `RectangularConcrete.calc_weight`), and add `self.g0k_b = self.g0k / self.b` right after line 687. | T's `SupStrucRectangular.calc_weight(spec_weight)` has a different signature. An override named `calc_weight` would also be hit by T's `RectangularConcrete.__init__` (`T:325`), which would feed a wrong self-weight into `set_loadBalancing` (`S:797`). T's `Member1D`/`Member2D` read `section.g0k_b`. |
| `S:699-700` `set_punching_reinforcement_volume` | **Delete**, unless 1A.7 (punching) is ported. | It calls a parent method that T doesn't have. |
| `S:953-967` `calc_punching_shear_resistance`, `S:969-976` `calc_punching_prestress_deviation_force` | **Delete**, unless 1A.7 is ported. | Same reason. |
| `S:1011` `system_drop = Slab(self.l_x, self.l_y, "drop_beam")` | Keep. | T's `Slab(length_x, length_y, support)` (`T:1418`) has the same signature, and `Workflow/260625_slab_properties.db` contains `drop_beam` for spans 3, 5, 6, 7, 8, 10, 12, 16 (**not 4**). |
| `S:688` and following: `self.cost_*`, `self.construction_time` | Keep; with 1.0.3 they evaluate to 0. | |

`PostTensionedConcrete` inherits from T's `RectangularConcrete`: `mu_unsigned`, `calc_shear_resistance`, `f_w_ger`, `Faktor_ger`, `as_bw`, `roh/rohs`. It sets `self.f_w_ger` as an instance float (`S:663/667`), which shadows the static method on the instance only. T's members call `RectangularConcrete.f_w_ger(...)` on the class, so that's fine.

### 1A.3 `Member2D.__init__` (T:1717): deflections for `pc`
T's `Member2D` computes `w_install`, `w_use` and `w_app` from `self.unit_def`. Add the PT branches from S, replacing `unit_def` → `self.unit_def`:

| Copy from S | Insert into T |
|---|---|
| `S:2943-2950` (`elif section_material == "pc":` … `self.w_install = unit_def_pc * …`) | inside the `if self.requirements.install == "ductile":` block (after `T:1781`), as `if section_material == "pc":` |
| `S:2967-2974` (`elif section_material == "pc":` → `self.w_use`) | after `T:1806` (`self.w_use = self.unit_def * …`) |
| `S:2982-2989` (`elif section_material == "pc":` → `self.w_app`) | after `T:1817` (`self.w_app = self.unit_def * …`) |

Also, at `T:1774-1777` T calls `RectangularConcrete.f_w_ger(self.section.roh, …)` unconditionally. That works for PT, which has `roh/rohs/h/d`.

Existing bug, unrelated to PT: in the `brittle` branch (`T:1797`, `T:1800`) T uses `unit_def` instead of `self.unit_def`, which raises a `NameError` for `install="brittle"`.

### 1A.4 `Member2D.calc_qu` (T:1858): PT branch
T's `calc_qu` reads `section.qs_class_n_y`, `mu_max_y` and so on (`T:1869`), which PT doesn't have. Insert S's PT branch **before** `T:1869`:

| Copy from S | Insert into T | Changes |
|---|---|---|
| `S:3065-3114` (`if self.section.section_type == "pc_rec":` … `return finalize(qu_bend, qu_shear)`) | at the top of `Member2D.calc_qu`, after `T:1868` | 1) Before the block, add `alpha_m = self.system.alpha_m_x` (S gets it from `uls_redistributed_moment_factors`). 2) Replace `if self.should_check_punching(): … else: qu_shear = self.calc_shear_qu()` with `qu_shear = self.calc_shear_qu()`. 3) Replace `return finalize(qu_bend, qu_shear)` with `return min(qu_bend, qu_shear)`. |
| `S:3157-3180` (`calc_shear_qu`, `calc_shear_prestress_deviation_force`, `calc_shear_secondary_force`) | as new methods of T's `Member2D`, after `calc_qu` (before `T:1920`) | None. `hasattr` guards make them safe for `rc_rec` too. |

`Member2D.__init__` calls `self.calc_qu()` at `T:1746`, before the deflections. That's fine, because PT computes everything in its constructor.

### 1A.5 `Member2D.get_fire_resistance` (T:1969)
Add after the `rc_rec` branch (`T:1971-1972`):
```python
elif self.section.section_type == "pc_rec":
    fire_resistance = PostTensionedConcrete.fire_resistance(self.section)
```
(This is `S:3405-3406`.)

### 1A.6 Optimizer: `Workflow/struct_optimization_2D.py`
T's 2D optimizer only knows `rc_rec`. Copy S's PT optimizer and its helpers:

| # | Copy from S (`S:core/struct_optimization_2D.py`) | To T (`Workflow/struct_optimization_2D.py`) | Changes |
|---|---|---|---|
| a | `:3` add `OptimizeResult` to the scipy import | `T:3` | — |
| b | `:6-17` (penalty constants) | after the T imports (`T:5`) | — |
| c | `:19-35` (`uls_infeasible_penalty`, `pt_min_reinforcement_penalty`) | after (b) | — |
| d | `:55-123` (`invalid_rectangular_geometry`, `unique_start_points`, `best_basinhopping`) | after T's `RandomDisplacementBounds` (ends ~`T:28`) | `best_basinhopping` uses `RandomDisplacementBounds`. T has the same class. |
| e | `:125-194` (`rectangular_feasible_start`) | after (d) | — |
| f | `:196-270` (`calc_uls_penalty`, `calc_sls1_penalty`, `calc_sls2_penalty`, `calc_fire_penalty`, `criterion_penalty`) | after (e) | In `calc_sls1_penalty`, `struct_analysis.concrete_member_is_uncracked` needs 1.0.2b. PT calls it with `use_cracked_deflection=False`, so it isn't reached there. |
| g | `:391-467` (`opt_pc_rec`) and `:469-520` (`pc_rqs`) | before T's `get_optimized_section` (`T:177`) | **Remove the Member2D kwargs T doesn't support** in both `Member2D(...)` calls (`:428-433` in `make_seed_member`, `:497-502` in `pc_rqs`): `evaluate_service=…`, `check_punching=…`, `uls_bending_only=…`, `optimize_shear_reinforcement=…`. **Delete** `member.apply_required_punching_reinforcement()` (`:504`), unless 1A.7 is ported. |
| h | `:855-858` (the `elif … == "pc_rec":` branch) | into T's `get_optimized_section` after `T:181` | — |

### 1A.7 (Optional) Punching shear for point-supported PT and RC slabs
This only matters for `PL-eingespannt` / `drop_beam`. Copy:
- `S:core/struct_analysis.py:417-434` (`set_punching_reinforcement_volume`), `:546-604` (`calc_punching_shear_resistance`, `calc_punching_shear_reinforcement_resistance`) → T's `RectangularConcrete`
- `S:3010-3011` (`should_check_punching`), `:3182-3335` (all `calc_punching_*`, `calc_required_punching_shear_reinforcement_resistance`, `apply_required_punching_reinforcement`) → T's `Member2D`
- `S:2393-2404` (the `Slab.__init__` extra args `column_width/length/ke/tributary_area` and `has_columns`) → T's `Slab.__init__` (`T:1418`)
- Then keep the PT lines deleted in 1A.2 and 1A.6g, and the `should_check_punching()` branch in 1A.4.

### 1A.8 Driver: `Workflow/plot_datasets_2D.py` and `Workflow/slab_2d_optimization.py`
- Copy the `elif crsec_type == "pc_rec":` block `S:core/plot_datasets_2D.py:211-248` into T's `plot_dataset` loop, after the `rc_rec` branch (`T:Workflow/plot_datasets_2D.py:72-123`). Adapt it to T's loop: T already has `mech_prop` and `prod_id_str`. S's rebar query filters on `Statistik = 1`, which doesn't exist in T; use T's `ValidEPD = 1 AND Man_Ausschluss = 1`. Define `pt_layout = [1, 0, 1, 0]` (drop beams in x and y) or pass it in as a parameter.
- In T's re-creation block (around `T:Workflow/plot_datasets_2D.py:185-195`, the `Member2D(...)` → `get_optimized_section` loop), nothing needs to change: it calls `struct_optimization_2D.get_optimized_section`, which now dispatches `pc_rec`.
- In `plot_section` (`T:Workflow/plot_datasets_2D.py:320`), extend `if section.section_type == "rc_rec"` to `in ("rc_rec", "pc_rec")`, and copy the tendon drawing and PT legend lines `S:core/plot_datasets_2D.py:520-521` and `530-532`, plus `plot_pt_tendons` (`S:697-702`).
- In `Workflow/slab_2d_optimization.py`, add a call with `"pc_rec"` and `mat_names = ["'ready_mixed_concrete'"]`. `database_name` already points to `database_261009.db` (done 2026-10-09).

### 1A.9 Verification
```bash
cd Workflow && python - <<'EOF'
import struct_analysis as sa
db = "database_261009.db"
c  = sa.ReadyMixedConcrete("'C30/37'", db); r = sa.SteelReinforcingBar("'B500B'", db); p = sa.PrestressingSteel("'Y1860'", db)
s  = sa.PostTensionedConcrete(c, r, p, 8, 8, 1.0, 0.24, 0.01, 0.15, 0.01, 0.15, layout=[1,0,1,0])
sys = sa.Slab(8, 8, "PL-eingespannt")
fs = sa.FloorStruc([...], db)   # same floor build-up as in slab_2d_optimization.py
m  = sa.Member2D(s, sys, fs, sa.Requirements(), 0.75e3, 2e3); m.calc_qk_zul_gzt()
print(s.Px_total, s.mu_max, s.mu_min, m.qu, m.qk_zul_gzt, m.w_app, s.co2)
EOF
```
Compare against S with the same inputs: `cd /Users/luizlindzus/SDSD_Bieg && python checks/check_pt_2d.py`. Expect differences only from `creep_coef` 2.0 vs 2.5, costs, and T's minimum-reinforcement logic in `RectangularConcrete`.

---

## 1B Timber-concrete composite (`tcc`, 1D)

TCC works **per metre width**: `g0k` is in N/m², `EI` is per m, `Mu`/`Vu` are per m. T's `Member1D` multiplies by `section.b` (`T:1462-1463`: `gk = g0k + g1k*b + g2k*b`, `qk = qk*b`), so TCC must expose `b = 1.0`.

### 1B.1 Copy the classes
| Copy from S | To T |
|---|---|
| `S:core/struct_analysis.py:1693-2057` (`# ......` separator, `class SupStrucTCC`, `class TCC` including `calc_gamma`, `calc_EIeff`, `calc_mu`, `calc_vu`, `fire_resistance`, `fire_minimizer`, `remaining_section`) | `T:Workflow/struct_analysis.py`, after `RibWood` ends (`T:1307`), directly before the separator/`class MatLayer` at `T:1308-1310` |

### 1B.2 Changes inside the pasted TCC
| Where (S line) | Change | Why |
|---|---|---|
| `TCC.__init__`, after `S:1793` (`self.w = self.g0k`) | Add `self.b = 1.0` and `self.g0k_b = self.g0k` | T's `Member1D` reads `section.b` and `section.g0k_b` (`T:1458`, `T:1462`). |
| `SupStrucTCC.calc_weight` (`S:1730-1742`) | Keep. It uses `.specific_weight`, available after 1.0.3. | |
| `TCC.fire_minimizer` (`S:1982-2002`) | **Fix the existing bug:** at `S:1992` `return -qd_fire` is reached before `qd_fire` is assigned. Move `qd_fire = member.psi[2] * member.qk + member.gk` (`S:1997`) above the `if rem_sec is None:` check. | Raises `UnboundLocalError` when the section burns away. |
| `TCC.remaining_section` (`S:2004-2057`) | Keep. It uses `copy.deepcopy`, available after 1.0.2a. | |

### 1B.3 `Member1D.__init__` (T:1449): TCC deflections and vibration
Insert S's `tc` branches, replacing `unit_def` → `self.unit_def`:

| Copy from S | Insert into T |
|---|---|
| `S:2540-2544` (`if section_material == "tc": … self.w_install = …EI_SLS…`) | in the `ductile` block, after the `rc` branch (before `T:1517`) |
| `S:2556-2560` (same, for `brittle`) | in the `brittle` block, before `T:1540` |
| `S:2568-2571` (`tc` → `self.w_use`) | after the `rc` `w_use_ger` block (before `T:1558`) |
| `S:2578-2581` (`tc` → `self.w_app`) | after the `rc` `w_app_ger` block (before `T:1574`) |

And change `T:1581` from `if section_material == "wd":` to `if section_material in ("wd", "tc"):`. Otherwise `a_ed`, `wf_ed`, `ve_ed`, `ve_cd` and `r1` never exist for TCC, and `calc_sls2_penalty` (1B.6) raises `AttributeError`.

### 1B.4 `Member1D.calc_qk_zul_gzt` (T:1652)
TCC carries dummy `mu_max = vu_p = 1`. The real ULS capacity is computed from `Mu[0]/Mu[1]` and `Vu[0]/Vu[1]` (t=0 and t=∞) in S's TCC branch. Replace `T:1652-1653` with:
```python
def calc_qk_zul_gzt(self, gamma_g=1.35, gamma_q=1.5):
    if self.section.section_type == "tcc":
        # body of S:core/struct_analysis.py:2730-2755 (capacity at t=0 / t=inf, degree of utilisation)
        ...
    else:
        self.qk_zul_gzt = (self.qu - gamma_g * self.gk) / gamma_q
```
When pasting `S:2730-2755`:
- Replace `self.gamma_g` / `self.gamma_q` with the parameters `gamma_g` / `gamma_q`.
- Drop the `qu_*_bending` / `qu_*_shear` lines (`S:2734-2735`, `2741-2742`). Also leave out `component_qk_zul` (`S:2715-2728`) and the governing-mode lines (`S:2756-2761`), because T's `calc_qu` doesn't set `qu_bending` / `qu_shear`.

Only use TCC with `BeamSimpleSup`. In T's `calc_qu` (`T:1595`) the negative-moment branch would use `mu_min = 0` and `vu_n = 0`, which gives a capacity of 0 for continuous systems.

### 1B.5 `Member1D.get_fire_resistance` (T:1701)
Add before the `else:` at `T:1711`:
```python
elif self.section.section_type == "tcc":
    fire_resistance = TCC.fire_resistance(self)
```
(This is `S:2842-2843`.) `TCC.fire_resistance` needs `member.fire`, `psi`, `qk`, `gk`, `system.alpha_m/alpha_v/l_tot`; T's `Member1D` has all of them.

### 1B.6 Optimizer: `Workflow/struct_optimization.py`
| # | Copy from S (`S:core/struct_optimization.py`) | To T (`Workflow/struct_optimization.py`) | Changes |
|---|---|---|---|
| a | `:3` `OptimizeResult` | T's scipy import (`T:3`) | — |
| b | `:7-12` (penalty constants) | after T's imports (`T:7`) | — |
| c | `:15-35` (`uls_infeasible_penalty`, `calc_sls2_penalty`) | after (b) | — |
| d | `:578-776` (`tcc_feasible_start`, `best_tcc_basinhopping`, `opt_tcc`, `tcc_rqs`) | before T's `get_optimized_section` (`T:1288`) | In `opt_tcc`/`make_seed_member` (`:680`) and `tcc_rqs` (`:726`), **replace** `fire=m.fire` / `fire=fire` with `fire_b=bool(fire[0]), fire_l=bool(fire[1]), fire_t=bool(fire[2]), fire_r=bool(fire[3])`, because T's `Member1D` has no `fire=` kwarg. `best_tcc_basinhopping` uses T's existing `RandomDisplacementBounds` (`T:10`). |
| e | `:793-796` (the `elif … == "tcc":` branch) | into T's `get_optimized_section` before the `else:` (`T:1308`) | Call it as `return opt_tcc(member, to_opt, criterion, max_iter)`. T's extra `alg` / `fixed_params` arguments are simply not passed. |
| f | `:889-910` (`get_opt_sec` `tcc` branch) and `:952-967` (`tcc_crsc`) | into T's `get_opt_sec` (`T:1317`) / after `rc_rib_crsc` | Only needed for the GWP-budget plot (`plot_section_dataset`). |

### 1B.7 Driver: `Workflow/opt_and_plot.py` and a run script
- In `plot_dataset` (`T:Workflow/opt_and_plot.py:32`, the `for mat_name in mat_names:` loop), add at the **top of the loop body** a TCC branch modelled on `S:core/plot_datasets.py:226-261`. There, `mat_name` is a tuple `(concrete_material, wood_material, connector_name)`. Create one `ConnectorTCC`, then low/high-GWP concrete, wood and rebar, then `TCC(concrete, rebar, timber, connector, s=0.4, a_ribs=0.2, h_c=0.08, h_w=0.12, b_w=0.2, d=0.0, l0=2)`, and `continue`. Replace S's `selected_epd_extreme_product_ids` with T's own `ValidEPD = 1 AND Man_Ausschluss = 1` query (`T:34-41`).
- In the legend block (`T:Workflow/opt_and_plot.py:275-282`), add `elif i[0].section_type == "tcc": material_lg = i[0].concrete_type.mech_prop + " + " + i[0].wood_type.mech_prop + " + " + i[0].connector_type.name`.
- In `plot_section` (`T:507`), add a `tcc` branch from `S:core/plot_datasets.py:658-673`.
- New run script `Workflow/<date>_Anwendung_TCC.py`, modelled on `Workflow/260730_Anwendung_Timber.py` and `S:examples/beam_1d_tcc_mives.py`: `crsec_type = "tcc"`, `mat_names = [("'ready_mixed_concrete'", "'Glue_laminated_timber'", "'DBS_8'")]`, `system = "Simple Beam"`, and a floor build-up with an acoustic layer, as S does.

### 1B.8 Verification
```bash
cd Workflow && python - <<'EOF'
import struct_analysis as sa
db = "database_261009.db"
c = sa.ReadyMixedConcrete("'C30/37'", db); r = sa.SteelReinforcingBar("'B500B'", db)
w = sa.Wood("'GL24h'", db); k = sa.ConnectorTCC("'DBS_8'", db)
s = sa.TCC(c, r, w, k, 0.4, 0.6, 0.10, 0.24, 0.14, 0.0, 6.0)
m = sa.Member1D(s, sa.BeamSimpleSup(6.0), sa.FloorStruc([...], db), sa.Requirements(), 0.75e3, 2e3)
m.calc_qk_zul_gzt(); m.get_fire_resistance()
print(s.EI_SLS, s.Mu, s.Vu, m.qk_zul_gzt, m.w_app, m.f1, m.fire_resistance, s.co2)
EOF
```
Compare against S: `cd /Users/luizlindzus/SDSD_Bieg && python checks/check_tcc_1d.py` and `pytest tests/test_sls2_tcc_regression.py tests/test_tcc_reinforcement_layers.py`.

---

## 1C Suggested order of work
1. Create a branch `feature/add-pt-tcc` from `main` (after or independently of `cleanup/archive`).
2. 1.0 (database and material aliases): commit.
3. 1B (TCC): it's 1D and touches fewer files. Verify with 1B.8, then commit.
4. 1A.1–1A.6 (PT without punching): verify with 1A.9, then commit.
5. 1A.8 (PT driver) and optionally 1A.7 (punching).

---

# Section 2: What T does not implement yet, compared to S

## Cross-sections and materials
- **Post-tensioned concrete slab** `pc_rec`: `PostTensionedConcrete` and `PrestressingSteel`, with load balancing, tendon layout (drop beams / distributed), secondary moments, PT cracking moment and effective stiffness (`calc_EIeff`), and PT fire table.
- **Timber-concrete composite** `tcc`: `TCC`, `SupStrucTCC` and `ConnectorTCC`, using the γ-method at t=0/t=∞ (ULS and SLS), creep interpolation, connector stiffness `K_ser`, and a charring model with connector-stiffness reduction in fire.
- **RibWood hollow-core insulation:** glass wool in the box cavities, counted in GWP, cost and time (`S:1553-1585`).
- **RibbedConcrete:** negative bending with different widths (`mu_unsigned_different_widths`), formwork factor and cost, and a hard-coded spreading reinforcement in the quantities.
- **Construction cost and time:** S reads `Cost` and `T_construction` from the DB for every material and adds formwork cost/time. T sets `cost = 0` everywhere and has no time model.
- **Material `specific_weight` from EPD density:** T uses `density_load` from `material_prop`.

## Structural checks
- **Punching shear** (SIA 262, level of approximation 2): resistance, punching reinforcement, required `V_Rd,s`, and steel volume, cost and GWP added to the section.
- **Plastic moment redistribution** for `LL-eingespannt` / `PL-eingespannt` slabs (`uls_redistributed_moment_factors`).
- **Shear with prestress deviation forces** and secondary shear (`calc_shear_qu` and helpers).
- **Smooth ductility factor** for RC in `Member2D.calc_qu`. T sets `qu_bend = 0` on failure; S keeps an arctan transition, which is better for the optimizer.
- **ULS governing-mode tracking** (`qu_bending`, `qu_shear`, `uls_governing_mode`, `qk_zul_bending_gzt`, `qk_zul_shear_gzt`).
- **Member2D vibration (SLS2):** S computes `f1` with ν and `kf2` from the DB, plus `a_ed`, `wf_ed`, `ve_ed`. T disables this (`f1 = 100`, `a_ed = 0`).
- **Member1D vibration for concrete:** S runs it for `wd`, `rc` and `tc`; T only for `wd`.
- **`Slab` coefficients:** S reads `kf2` (column `F`) from the DB and derives `alpha_w_f_cd`. T hard-codes `kf2 = 1.0` and `alpha_w_f_cd = 10000`.
- **`Slab` support/column parameters:** `has_columns`, `column_width/length`, `column_ke`, tributary area, plus result caching and a clear error message for missing DB rows.
- **Fire in `Member2D`** for `pc_rec`.
- **`LoadCombinations` class:** a central ULS/SLS combination object; T computes the combinations inline.
- **`evaluate_service` / `uls_bending_only` switches** in `Member2D`, which skip SLS during ULS optimization for speed.

## Floor build-up and acoustics
- **`AcousticFloorGenerator`, `AcousticResult`, `AcousticRequirements`:** airborne (Rw) and impact (Ln,w) sound for each section type, floating screed, gravel damping, TCC branch, and automatic generation of a build-up that meets "normal" or "increased" requirements. `Member1D`/`Member2D` then report `acoustic_verified`.

## Optimization
- **Penalty framework** (`criterion_penalty`, `calc_*_penalty` with weights, ULS guard) and a **FIRE criterion** (S: ULS, SLS1, SLS2, FIRE, ENV).
- **Feasible-start search** (`rectangular_feasible_start`, `tcc_feasible_start`), multi-start `best_basinhopping` and an evaluation cache.
- **2D optimizers** for `pc_rec`, plus `rc_rib` / `wd_rib` / `wd_rec` in 2D. T's `struct_optimization_2D.py` only has `rc_rec`.
- T has things S lacks: Optuna/TPE (`alg="TPE"`), `fixed_params` for `wd_rib`, and continuous ribbed-slab optimization (`struct_optimization_RCrib_cont.py`).

## Evaluation and workflow (S only)
- **MIVES multi-criteria evaluation** (`S:core/MIVES.py`, `database/mives_260424.db`, `excel_sources/mives_weights_260424.xlsx`).
- **`final_comparison/`:** residential vs office system comparison, uncertainty quantification (`run_comparison_uq.py`, `run_pairwise_uq.py`), GWP drivers, GWP vs cost, application-range plots, cross-section catalogue, web-app data export.
- **`core/paths.py`:** central path handling, so scripts run from any working directory and a missing DB raises an error instead of creating an empty file.
- **Database builders** from Excel (`database/build_material_database.py`, `build_slab_properties_database.py` from Cedrus coefficients `cedrus_slab_coefficients_260507.xlsx`).
- **Tests and checks:** `tests/` (pytest regressions for SLS1 concrete, SLS2 TCC, damping defaults, TCC reinforcement) and `checks/` (scripted single-design checks).
- **Docs:** UML/architecture diagrams (`docs/diagrams/`), README with a folder map.

## Things T has that S doesn't (keep them when porting)
- SIA 262:2025 deflection factor `Faktor_ger` (formula 104), and a minimum-reinforcement/minimum-thickness logic in `RectangularConcrete` (`as_min`, `hmin_c`).
- `FlatSlab2D`, with separate x/y reinforcement and resistances (`mu_max_y`, `qs_class_*_y`).
- `RibWood.calc_vu_detail` (shear of the composite section) and `RibbedConcrete.mu_unsigned_4l`.
- Optuna/TPE optimization and continuous ribbed slabs.
