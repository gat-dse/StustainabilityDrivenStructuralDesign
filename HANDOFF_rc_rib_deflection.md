# Handoff: rc_rib, generic code reads slab values instead of rib values

Status 2026-11-08: analysed in detail, **not fixed**.

Line numbers refer to the working tree on 2026-11-08 (with the uncommitted changes in `struct_analysis.py`).
All files are in `Workflow/`.

---

## 1. Summary

`Member1D`, the optimizers and the plots were written for `RectangularConcrete`. In that class, the generic names
(`d`, `ds`, `x_p`, `x_n`, `vu_p`, `vu_n`, `mr_p`, `mr_n`, `as_p`, `as_n`) describe the one and only cross-section.

`RibbedConcrete` has two structural elements: the **slab** (Platte, flange, thickness `h_f`, transverse direction) and
the **rib / T-beam** (Plattenbalken, full height `h`, main span direction). It kept the generic names for the **slab** and
stores the **rib** values under new names (`_PB` / `_pb`).

`Member1D` only reads the generic names. For an rc_rib section it therefore silently gets **slab values** wherever it
expects beam values. Some generic names do hold rib values (`mu_max`, `mu_min`, `qs_class_p/n`, `roh`, `rohs`, `ei1`,
`ei2`), so in several formulas slab and rib values are **mixed**.

Visible symptom: rc_rib (1D, simple beam, Schuettung) has **no feasible section from 6 m on**. All members fail `SLS1`,
and from 10 m most also fail `b_w`. More iterations do not help (200 TPE iterations: 4 m 9/9 feasible, 6–12 m 0/9). A
brute-force grid of 2,300 combinations at each of 4, 6, 8 and 12 m found no feasible section either.

| # | Bug | Where | Effect on results today |
|---|---|---|---|
| 1 | Cracked deflection uses slab `d` | `struct_analysis.py:1568–1647` | **Big.** Deflection grows with height, so SLS1 always fails from 6 m |
| 2 | ULS shear uses slab `vu` | `struct_analysis.py:1700, 1723` | **Big.** `qu` is capped by the slab shear, so ULS gets worse with height |
| 3 | Ductility factor uses slab `x`, `d`, `mr` | `struct_analysis.py:1693–1696, 1716–1719` | Medium. A brittle (under-reinforced) rib keeps its full `mu_max` |
| 4 | Cracked/uncracked decision uses slab `mr` | `struct_analysis.py:1736`, `struct_optimization_RCrib_cont.py:200–206, 403–409` | None in the main workflow; wrong in `RCrib_cont` |
| 5 | `rohw` uses slab `d` and has a unit error | `struct_analysis.py:877` | None (value is never used) |

---

## 2. Background: names and definitions in `RibbedConcrete`

### Geometry (base class `SupStrucRibbedConcrete`, `struct_analysis.py:734–740`)

| Name | Meaning |
|---|---|
| `h` | total height (slab + rib) |
| `h_f` | flange height = slab thickness |
| `h_w = h - h_f` | web (rib) height below the slab |
| `b` | flange / slab width (rib spacing) |
| `b_w` | **rib width** |

### Reinforcement (`struct_analysis.py:813–816`)

| Name | Meaning |
|---|---|
| `bw = [[Ø, s], [Ø, s]]` | slab bending reinforcement, bottom layer (1. Lage) and top layer (4. Lage). "bw" = *Bewehrung*, **not a width** |
| `bw_bg = [0, 0.15, 2]` | slab stirrups (none) |
| `bw_r = [Ø, n, n_layers]` | rib longitudinal bars at the **bottom of the web** ("im Steg") |
| `bw_bg_r = [Ø, s, n_legs]` | rib stirrups |

Careful: in `calc_shear_resistance` (`struct_analysis.py:1024`) `bw = self.b` is a local variable for the slab width, and in
`SupStrucRibWood` (`struct_analysis.py:1115`) `self.bw` really is the rib width.

### Static depths (`calc_d`, `struct_analysis.py:917–926`)

The static depth is measured from the compressed face to the tension steel. `d` is for positive (sagging) moment, `ds`
for negative (hogging) moment.

| Name | Element | Formula | Line | Value (example `h_f = 0.13`) |
|---|---|---|---|---|
| `d` | slab, sagging | `h_f − c_nom − Ø_bottom/2` | 918 | ≈ 0.106 m, **constant**, independent of `h` |
| `ds` | slab, hogging | `h_f − c_nom − Ø_top/2` | 919 | ≈ 0.106 m |
| `d_PB` (1 layer) | rib, sagging | `h − c_nom − Ø_stirrup − Ø/2` | 921 | grows with `h` |
| `d_PB` (2 layers) | rib, sagging | `h − c_nom − Ø_stirrup − 1.5·Ø − c_nom` | 924 | see open question Q2 |
| `ds_PB` | rib, hogging | `h − h_f/2` (bottom of web to middle of flange) | 922, 925 | grows with `h` |

### Where slab and rib values are stored (`struct_analysis.py:819–878`)

| Quantity | Generic name = **slab** | Rib value | Line |
|---|---|---|---|
| static depth | `d`, `ds` | `d_PB`, `ds_PB` | 856 |
| cracking moment | `mr_p`, `mr_n` (`b·h_f²/6·fctm`) | `mr_pb_p`, `mr_pb_n` (`Iy/(h−z_s)·fctm`) | 819–823 |
| bending resistance | `mu_max_slab`, `mu_min_slab` (**never used**) | `mu_max`, `mu_min` ✅ generic name = rib | 859–862 |
| compression zone | `x_p`, `x_n` | `x_PB_p`, `x_PB_n` | 859–862 |
| steel area | `as_p`, `as_n` | `as_PB_p`, `as_PB_n` | 859–862 |
| ductility class | `qs_class_p_slab`, `qs_class_n_slab` | `qs_class_p`, `qs_class_n` ✅ | 859–862 |
| reinforcement ratio | `roh_slab` (**never used**) | `roh`, `rohs` ✅ | 863, 866–867 |
| shear resistance | `vu_p`, `vu_n` | `vu_PB_p`, `vu_PB_n` | 874–875 |
| stirrup area | `as_bw` (= 0) | `as_PB_bw` | 874–875 |
| stiffness | – | `ei1`, `ei2` ✅ (`ei2` uses `d_PB`, line 915) | |
| deflection factor | – | `Faktor_ger` ✅ (uses `d_PB`, line 870, but **not used** by `Member1D`) | 870 |

✅ = the generic name already holds the rib value (correct for `Member1D`).

---

## 3. The five bugs in detail

All example values below: C30/37, B500B, span 6 m simple beam, Schuettung, `g2k = 0.75 kN/m²`, `qk = 2 kN/m²`,
`b = 1.0`, `b_w = 0.3`, `h_f = 0.13`, slab Ø8 @ 150, rib 4 Ø26 in 1 layer, stirrups Ø8 @ 150 (2 legs).
Computed with `rib_mix.py` (see section 6).

### Bug 1: cracked deflection uses the slab `d` (causes the SLS1 symptom)

**Where:** `Member1D.__init__`, deflection block `struct_analysis.py:1562–1647`.

| Lines | Value | Used by |
|---|---|---|
| 1570–1573 | `f_w_ger_2`, `f_w_ger_0` (install, ductile) | stored only |
| **1581–1587** | **`w_install_ger`** (install, ductile) | optimizer, `failed_checks` |
| 1592–1595 | `f_w_ger_2`, `f_w_ger_0` (install, brittle) | stored only |
| **1604–1610** | **`w_install_ger`** (install, brittle) | optimizer, `failed_checks` |
| 1615–1618 | `f_w_ger_2`, `f_w_ger_0` (use) | stored only |
| **1626–1629** | **`w_use_ger`** | optimizer, `failed_checks` |
| 1633–1634 | `f_w_ger_2` (appearance) | stored only |
| **1643–1646** | **`w_app_ger`** | optimizer, `failed_checks` |
| 1575–1578, 1597–1600, 1620–1623, 1635–1639 | simplified version with `Faktor_ger` | commented out (`'''`) |

Every call is

```python
RectangularConcrete.f_w_ger(self.section.roh, self.section.rohs, phi, self.section.h, self.section.d)
```

and `f_w_ger` (`struct_analysis.py:480–482`) is

```python
f = ((1 - 20*rohs) / (10*roh**0.7)) * (0.75 + 0.1*phi) * (h/d)**3
```

**What is mixed:** `roh`, `rohs` and `h` are rib values. `d` is the slab value.

**Why it is wrong:** for rc_rib, `d` is the slab depth (≈ 0.106 m, constant). `h` grows with the rib, so `(h/d)³`
grows with the cube of the height. The deeper (stiffer) the rib, the larger the calculated deflection.

| h_w [m] | h [m] | d (slab) | d_PB | (h/d)³ now | (h/d_PB)³ correct | w_install_ger now [mm] | with d_PB [mm] | allowed [mm] |
|---|---|---|---|---|---|---|---|---|
| 0.04 | 0.17 | 0.106 | 0.129 | 4.1 | 2.3 | 74.1 | 34.9 | 17.1 |
| 0.20 | 0.33 | 0.106 | 0.289 | 30 | 1.5 | 247.8 | **9.5** | 17.1 |
| 0.40 | 0.53 | 0.106 | 0.489 | 125 | 1.3 | 435.6 | **3.6** | 17.1 |
| 0.80 | 0.93 | 0.106 | 0.889 | 675 | 1.1 | 923.3 | **1.4** | 17.1 |

With `d_PB` the deflection decreases with height and the section passes from about `h_w = 0.2` on.

**Where the wrong value goes:**
- `rc_rib_rqs` (`struct_optimization.py:762`): lines 832–835 always use `w_*_ger` for penalty2.
- `failed_checks` (`struct_optimization.py:1283`): lines 1296–1302 treat rc_rib as always cracked and use `w_*_ger`.

**Consequence:** all rc_rib SLS1 results so far are unusable. The few 4 m "winners" only pass because a very shallow
section keeps `(h/d)³` small.

**Fix:** pass `d_PB` instead of `d` (see section 4).

### Bug 2: ULS shear of the rib checked with the slab shear resistance

**Where:** `Member1D.calc_qu`, `struct_analysis.py:1700` (positive branch) and `1723` (negative branch).

```python
qu_shear = self.section.vu_p / (max(alpha_v) * self.system.l_tot)    # 1700
qu_shear = self.section.vu_n / (min(alpha_v) * self.system.l_tot)    # 1723
return min(qu_bend, qu_shear)                                        # 1724
```

**What is mixed:** `qu_bend` uses the rib `mu_max`, and `qu_shear` uses the **slab** `vu_p`. `qu` is the minimum of both.

**How the two shear values are calculated** (`calc_shear_resistance`, `struct_analysis.py:1012–1061`):
- `'Platte'` branch (→ `vu_p`, `vu_n`, line 874): `as_bw = 0` → `vu_unsigned` without stirrups: `vrd = kd · tcd · dv`
  with the slab `d`. This is a resistance **per metre width**; neither `b` nor `b_w` appears.
- `'Plattenbalken'` branch (→ `vu_PB_p`, `vu_PB_n`, line 875): with the rib stirrups `as_PB_bw`, width `b_w`, depth
  `d_PB`: `min(vrds, vrdc)`. This is the actual rib resistance.

The rib values `vu_PB_p` / `vu_PB_n` are **never read** by `Member1D`.

**Effect:**

| h_w [m] | vu_p slab [kN] | vu_PB_p rib [kN] | qu now [kN/m] | qk_zul_gzt now [kN/m] |
|---|---|---|---|---|
| 0.04 | 82.1 | 30.9 | 21.7 | 8.3 |
| 0.20 | 82.1 | 77.5 | 27.4 | 11.0 |
| 0.40 | 82.1 | 135.8 | 27.4 | 9.7 |
| 0.80 | 82.1 | 252.3 | 27.4 | 7.0 |

- From `h_w ≈ 0.2` on, `qu` is fixed at 27.4 kN/m by the slab shear, whatever the rib does. Example `h_w = 0.4`:
  `qu_bend` = 95.6, `qu_shear` (slab) = 27.4, `qu_shear` (rib) would be 45.3.
- Because `qu` is constant but the self-weight grows, `qk_zul_gzt` **decreases** with height (11.0 → 7.0). Like
  bug 1, ULS gets worse for deeper sections.
- For shallow ribs it is unconservative: at `h_w = 0.04` the rib only has 30.9 kN, but 82.1 kN is used. (Here bending
  governs, so it does not show yet.)
- The slab `vu_p` does not depend on `b` (`b = 0.6 / 1.0 / 2.0` → 82.1 / 82.1 / 82.0 kN), but the load is per rib
  (`gk`, `qk` × `b`, lines 1532–1534). So for wide rib spacings the ULS check is even more off.
- Stirrup diameter, spacing and `b_w` have **no effect** on `qu`, so the optimizer cannot use them to fix ULS.

**Affects:** `qu` → `qk_zul_gzt` (line 1727) → penalty1 in `rc_rib_rqs` (`struct_optimization.py:818`) and "ULS"
in `failed_checks` (`struct_optimization.py:1292–1293`).

**Fix:** use `vu_PB_p` / `vu_PB_n` for rc_rib.

### Bug 3: ductility factor uses slab `x`, `d` and `mr`

**Where:** `Member1D.calc_qu`, positive branch `struct_analysis.py:1693–1696`, negative branch `1716–1719`.

```python
x_d = self.section.x_p / self.section.d                                                      # 1693
factor = min(0.5*(1 + 2/np.pi*np.arctan((self.section.mu_max - self.section.mr_p)/epsilon)), # 1694
             1 - 0.5*(1 + 2/np.pi*np.arctan((x_d - shift)/epsilon)))                          # 1695
qu_bend = factor * self.section.mu_max / (max(alpha_m) * self.system.l_tot**2)               # 1696
```

**When it runs:** only if the rib does **not** meet the required ductility class (`qs_class_vorh > qs_class_erf`,
lines 1677/1703). The trigger `qs_class_p` is a rib value, so the trigger is correct. With `qs_cl_erf = [3, 3]` (simple
beam) it only runs when the rib has class 99: `mu < mr` (brittle), `x/d > 0.5`, or `x > h_f` (then `mu_PB = 0` already,
line 997–1000).

**What the factor is supposed to do:** smooth 0/1 step (arctan with `epsilon = 1e-3`), so the optimizer has a gradient:
1. term 1 ≈ 1 if `mu_max > mr`: enough reinforcement, no brittle failure;
2. term 2 ≈ 1 if `x/d < shift` (0.35 or 0.5): ductile enough.

If either term is ≈ 0, `qu_bend` ≈ 0.

**What is mixed:**

| Term | Used now | Belongs to | Correct |
|---|---|---|---|
| `mu_max` | `mu_max` | rib ✅ | `mu_max` |
| `x_p` | `x_p` | slab ❌ | `x_PB_p` |
| `d` | `d` | slab ❌ | `d_PB` |
| `mr_p` | `mr_p` (`b·h_f²/6·fctm`) | slab ❌ | `mr_pb_p` |
| (neg.) `x_n / d` | slab, and **`d` instead of `ds`** | slab ❌ | `x_PB_n / ds_PB` |
| (neg.) `mr_n` | slab ❌ | | `mr_pb_n` |

**Why it is wrong:**
- Term 1 compares the rib resistance with the **slab** cracking moment (≈ 8 kNm). Nearly every rib has `mu_max > 8 kNm`,
  so the rib's minimum-reinforcement check is effectively switched off.
- Term 2 checks the **slab** ductility. A normal slab has `x/d ≈ 0.08`, so the term is always ≈ 1, independent of the rib.
- Result: `factor ≈ 1`, and a rib that is classified as not ductile keeps its **full** bending resistance.

**Example (under-reinforced deep rib, class 99 because `mu_max < mr_pb_p`):**

| Section | mu_max [kNm] | mr_p slab | mr_pb_p rib | factor now | factor correct | qu now [kN/m] |
|---|---|---|---|---|---|---|
| h_w 0.8, 1 Ø10 | 30.6 | 8.2 | 160.7 | 1.00 | 0.00 | 6.8 |
| h_w 0.8, 2 Ø12 | 87.9 | 8.2 | 160.7 | 1.00 | 0.00 | 19.5 |
| h_w 0.6, 2 Ø10 | 47.5 | 8.2 | 100.1 | 1.00 | 0.00 | 10.5 |

These sections would fail brittle, but they get full capacity. The optimizer may choose them when bending governs.

**Also in the negative branch (all rc sections):** the trigger in line 1703 is
`if qs_class_vorh[1] <= qs_class_erf[1]`, i.e. the **positive** class (field), although this branch checks the hogging
moment with `mu_min`. It should be `qs_class_vorh[0] <= qs_class_erf[0]`. The `shift` in line 1713 already uses
`qs_class_vorh[0]`.

**Also for rc_rec:** line 1716 divides `x_n` by `d` instead of `ds`. For rc_rec both are close (only the bar diameter
differs), but it is still wrong. The negative branch only runs if `abs(alpha_m[1]) < abs(alpha_m[0])` (cantilever,
continuous beam), not for the simple beam.

**Fix:** use `x_PB_p / d_PB`, `mr_pb_p` (positive) and `x_PB_n / ds_PB`, `mr_pb_n` (negative). For rc_rec use `ds` in
line 1716. In line 1703 use index `[0]`.

### Bug 4: cracked/uncracked decision uses the slab cracking moment

**Where:**
- `Member1D.calc_f1`, `struct_analysis.py:1736`:
  ```python
  if self.mkd_p < self.section.mr_p and self.mkd_n > self.section.mr_n:   # uncracked → ei1, else ei2
  ```
- `struct_optimization_RCrib_cont.py:200–206` and `403–409`: uncracked `w_*` if `mkd < mr`, else cracked `w_*_ger`.

**What is mixed:** the acting moment of the rib (`mkd_p`, line 1549: `alpha_m · (gk + qk) · l²`, load per rib) is
compared with the **slab** cracking moment.

**Example:** `h_w = 0.4`: `mkd_p` = 51.8 kNm, slab `mr_p` = 8.2, rib `mr_pb_p` = 52.9. The code says cracked, but the
rib is actually still uncracked.

The slab `mr` is so small that every rib is always classified as cracked.

**Effect today:**
- `calc_f1` → `f1`: not used for concrete, because the vibration check is switched off (`penalty3 = 0` in `rc_rib_rqs`,
  only `wd_*` in `failed_checks`). **No effect** now, but wrong as soon as vibration is switched on for concrete.
- `struct_optimization_RCrib_cont.py`: always uses the cracked deflection (and with bug 1 also the wrong one).
- `rc_rib_rqs` and `failed_checks` are **not affected**: they always use the cracked deflections for rc_rib (the
  uncracked option is commented out in `rc_rib_rqs`, lines 822–829).

**Fix:** use `mr_pb_p` / `mr_pb_n`. Then consider whether `rc_rib_rqs` / `failed_checks` should also choose
cracked/uncracked like rc_rec (`failed_checks` line 1297).

### Bug 5: `rohw` (stirrup ratio of the rib) uses the slab `d` and has a unit error

**Where:** `RibbedConcrete.__init__`, `struct_analysis.py:877–878`:

```python
self.rohw = (self.as_PB_bw / self.b_w) / (0.9 * self.d)
self.rohw_min = 0.001 * (fck/30)**0.5 * 500/fsk        # SIA 262:2025, (116)
```

**What is wrong (two things):**
1. `self.d` is the slab depth. If anything, it should be `d_PB`.
2. Bigger problem: the division by `0.9·d` is wrong in itself. `as_PB_bw = π·Ø²/4 · n / s` (line 1032) is already the
   stirrup area **per metre length** [m²/m]. SIA 262 (116): `ρ_w = A_sw / (s · b_w)` = `as_PB_bw / b_w`, dimensionless.
   Dividing again by `0.9·d` gives a unit of 1/m. The rc_rec version does it without the division
   (`struct_analysis.py:458`: `rohw = as_bw / min(bw, 0.4)`). Your comment on line 877 already points at this.

| h_w [m] | rohw now (`/0.9d`) | with `/0.9d_PB` | correct `as_PB_bw/b_w` | rohw_min |
|---|---|---|---|---|
| any | 0.0234 | 0.0192 … 0.0028 | **0.0022** | 0.0010 |

Today's value is about 10× too large, so the minimum-stirrup check would pass far too easily.

**Effect today:** none. `self.rohw` / `self.rohw_min` are **not read anywhere**. The same wrong formula also exists in
`RibbedConcrete.vu_unsigned` (`struct_analysis.py:1077`, there with `d_PB`), but there it only prints a warning.

**Fix:** `self.rohw = self.as_PB_bw / self.b_w` (and the same in line 1077). Then decide whether the check should become
a real constraint (penalty / `failed_checks`).

---

## 4. Proposed fix (not applied)

**Option A (recommended): fix the interface in `RibbedConcrete`.**
Rename the slab values to explicit names (`d_slab`, `ds_slab`, `x_p_slab`, `x_n_slab`, `vu_p_slab`, `vu_n_slab`,
`mr_p_slab`, `mr_n_slab`, `as_p_slab`, ...) and store the rib values under the generic names that `Member1D` reads
(`d = d_PB`, `ds = ds_PB`, `x_p = x_PB_p`, `vu_p = vu_PB_p`, `mr_p = mr_pb_p`, ...).
Then `Member1D`, `rc_rib_rqs`, `failed_checks`, `RCrib_cont` and the plots work without changes, and bugs 1–4 are fixed
together. Fix bug 5 at the same time.

Watch out: inside `RibbedConcrete` all slab calculations must be switched to the `_slab` names, otherwise the slab
breaks: `calc_mu` (uses `self.d`, `self.ds`, `self.mr_p`, `self.mr_n`), `calc_shear_resistance('Platte')`,
`roh_slab`, `as_min` / `di_xu_min`, and the CO₂ / cost sums that use `as_p`, `as_n`, `as_bw`.

**Option B (quick, only bug 1): pick the static height in `Member1D`.**

```python
d_def = getattr(self.section, "d_PB", self.section.d)   # rc_rib: d_PB, rc_rec: d (unchanged)
```

and pass `d_def` instead of `self.section.d` in all `f_w_ger` calls of the deflection block. Bugs 2–5 stay open, and
the same bug comes back every time new code reads `section.*`.

**After the fix:** rerun rc_rib (e.g. 1D template, `max_iter` 200, default lengths) and check that:
- the deflection decreases with `h_w` (table in bug 1, "with d_PB" column),
- `qu` changes with `h_w`, `b_w` and the stirrups (rib shear is active),
- an under-reinforced rib (table in bug 3) gets `qu_bend ≈ 0`,
- add a small test: build one `RibbedConcrete` + `Member1D` and assert that `Member1D` uses `d_PB`, `vu_PB_p`,
  `mr_pb_p`.

---

## 5. Open questions (with the supervisor)

- **Q1: Is the slab itself checked anywhere?** `mu_max_slab`, `mu_min_slab` and `roh_slab` are computed but never used.
  Today the slab is only "checked" by accident through bugs 2–4. After option A it is not checked at all unless that
  is added on purpose (transverse bending + shear of the slab between the ribs). Also, slab continuity is missing
  (comment at line 928).
- **Q2: `d_PB` with two layers** (line 924) subtracts `c_nom` twice. The second `c_nom` is apparently the clear spacing
  between the two layers, and `d_PB` then goes to the centre of the **upper** layer, not to the centroid of both layers.
  For equal layers the centroid would be `c_nom + Ø_stirrup + Ø + a/2` (`a` = clear spacing). The current version puts
  the bars about `Ø/2 + c_nom/2` too high (≈ 28 mm for Ø26, c = 30 mm), which is conservative. Should `a` be
  `max(Ø, d_max, 20 mm)` instead of `c_nom`?
- **Q3: `ds_PB = h − h_f/2`** assumes the hogging tension steel acts at mid-slab. OK as a simplification?
- **Q4: `RibbedConcrete.f_w_ger`** (line 1083) is marked "ÜBERNOMMEN VON RECHTECK-QS, NICHT ANGEPASST": is the
  rectangular formula valid for the T-beam? (`Member1D` calls `RectangularConcrete.f_w_ger` anyway.)
- **Q5: `w_install_ger`** subtracts `q_per` inside the bracket (`... - self.q_per`, lines 1587, 1611): check against
  SIA 262.
- **Q6: `opt_rc_rib`** with `n_lagen = 2` and `n_x_w = 1`: `rc_rib_rqs` switches internally to 1 layer
  (`struct_optimization.py:797`), but the returned section is built from `best_params` with `n_lagen = 2`. This can cause
  a mismatch in `failed_checks` (`b_w`).

### Not affected for rc_rib (for completeness)
- `Member2D` (`struct_analysis.py:1798ff`): only used with `FlatSlab2D`.
- Plots `plot_datasets_2D.py` and `opt_and_plot.py` (`x_p/d`, `h - d`, `ds`): correct for rc_rec. If ever called with
  a rib section, they would show slab values (fixed automatically with option A).

---

## 6. Test scripts (scratchpad, temporary)

Run from `Workflow/` with `PYTHONPATH=. ../.venv/bin/python <script>`.

- `rib_mix.py`: slab vs rib values for bugs 1–5 (all tables in section 3)
- `rib_bug3.py`: ductility factor now vs correct (bug 3 table)

  `/private/tmp/claude-501/-Users-luizlindzus-StustainabilityDrivenStructuralDesign/f69b078a-6f41-41d4-91ee-16bae64a20db/scratchpad/`

- `rib_defl.py`: deflection and `d` vs `d_PB` against `h_w`
- `rib_grid.py`: brute-force feasibility grid (spans as arguments, e.g. `4 6 8 12`)

  `/private/tmp/claude-501/-Users-luizlindzus-StustainabilityDrivenStructuralDesign/53e5f50b-bafe-4e79-8cb0-ac660c2e34e7/scratchpad/`

The scratchpad folders are deleted at some point. Copy the scripts into the repo if you want to keep them.
