# Code for Project "Nachhaltigkeit im Tragwerksentwurf"
kfm research group, ibk, ETHZ

## Setup
Python 3.14 (python.org installer). Install the packages into a local environment:
```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
To activate the environment in a terminal (optional; the prompt then shows `(.venv)` and `python` uses the venv):
```bash
source .venv/bin/activate   # run from the repo root
deactivate                  # to leave it again
```
Activation only applies to the current terminal window. Calling `.venv/bin/python` directly (as in the steps below) works without activating.
In PyCharm, select `.venv/bin/python` as the project interpreter (Settings → Project → Python Interpreter → Add → Existing).

Requirements: numpy, scipy, pandas, openpyxl, matplotlib, seaborn, shapely, optuna (versions in `requirements.txt`).
Run scripts from inside `Workflow/`, because the databases are opened by relative path.

## How to run (step by step)
1. **Set up the environment** (once): see *Setup* above.
2. **Update the database** (only after changing the Excel):
   - Edit `Database/260811_Datenbankdefinition.xlsx` (sheets `products`, `material_prop`, `floor_struc_prop`) and save it in Excel, so the formula values (e.g. `ValidEPD`) are recalculated.
   - Convert it, from inside `Database/`:
     ```bash
     cd Database
     ../.venv/bin/python Convert_Excel_to_DB.py
     ```
   - Copy the new `database_261009.db` to `Workflow/`. The scripts only read the copy in `Workflow/`.
3. **Choose an input script** in `Workflow/`:
   - `261009_Template_Examples.py`: 1D members (simple beam / continuous / two span), concrete and timber. Recommended starting point. Copy it and switch datasets on or off in the `runs` list.
   - `slab_2d_optimization.py`: 2D slabs (`rc_rec` only). Needs at least two slab sizes in `length_x` / `length_y`.
   - Older 1D scripts: `260513_simple_span_1d_Concrete.py`, `260730_Anwendung_Timber.py`, `PB_Einfeld.py`, `TestAlgorithm.py`.
4. **Adjust the settings** at the top of the script:
   - `basetype = "epd"` (product EPDs) or `"kbob"` (generic KBOB v9.0 values).
   - `database_name = "database_261009.db"`.
   - `lengths`, `max_iter`, `criteria`, `optima`, loads `g2k` / `qk`, and (template) `alg` and the `runs` list.
5. **Run the script** from inside `Workflow/`:
   ```bash
   cd Workflow
   ../.venv/bin/python 261009_Template_Examples.py
   ```
6. **Check the results:**
   - Plots open in a matplotlib window.
   - Excel files go to `Workflow/Results/`: `Members_{crsec_type}_{system}_{floor}_{basetype}.xlsx` (1D) and `Members_2D_{support}_{basetype}.xlsx` (2D).

Background and known issues: `SUMMARY_KBOB_EPD.md` (EPD/KBOB, UBP/Graue Energie, open problems) and `SUMMARY_Template_Examples.md` (template).
