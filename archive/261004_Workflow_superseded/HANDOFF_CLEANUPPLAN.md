# Repo cleanup: keep the live Workflow pipeline, archive everything else

## Context
The repo has 5 copies of `struct_analysis.py`, ~30 loose root files, several `alt/` folders, and a full snapshot (`260513_Betonartikel_Copy`). The live code is in `Workflow/`; every commit since Aug 2026 touches only that folder. The goal is a branch that keeps only the current pipeline at the top level and moves everything else into a dated `archive/`. The branch gets proposed as a draft PR in the supervisor meeting. The work is only file moves (`git mv`, so history is kept), with no logic changes. Inside `Workflow/` the layout stays flat (minimal), so imports and relative database paths keep working.

## This session: write the plan and the handoff only, no changes
When this plan is approved, **no files are moved, no branch is created, and nothing is committed or pushed.** The only output is:
1. This plan (the full cleanup, below), so it can be carried out later.
2. `HANDOFF.md` at the repo root, left untracked. It holds only the next steps and open issues, not this plan:
   - **Next steps:**
     1. Discuss the cleanup plan with the supervisor.
     2. If approved: create `cleanup/archive` and run the steps below.
     3. Review `git diff --cached -M --stat`, then commit and push the branch, and open a draft PR.
     4. Point `slab_2d_optimization.py` at `database_260811.db` (same tables) and test-run the 2D pipeline.
     5. Get `260811_Datenbankdefinition.xlsx` into the repo: force-add it, or add a `!Database/*.xlsx` exception to `.gitignore`.
     6. Later: a central `paths.py` for DB paths, like the other thesis.
     7. Later: port the missing slab types (post-tensioned `pc_rec`, timber-concrete composite `tcc`) and punching shear from the other thesis.
   - **Open issues:**
     - `opt_and_plot.py` imports root `class_to_excel.py`, which works only through PyCharm's `sys.path`.
     - The 2D script opens `database_260506_Hochbau.db`, which is not in `Workflow/`.
     - `Convert_Excel_to_DB.py` needs `260811_Datenbankdefinition.xlsx`, which is not in the repo or on disk.
     - Several scripts open `database_260610_Hochbau.db` / `database_260617_Hochbau.db` / `database_260506_Hochbau.db` from the wrong folder or files that don't exist.
     - Multiple divergent copies of `struct_analysis.py` exist; `Workflow/` is the current one.

## The live pipeline (what stays)
```
Run scripts (Workflow/)                         Core (Workflow/)
 260513_simple_span_1d_Concrete.py  (rc) ─┐
 260730_Anwendung_Timber.py         (wd) ─┼─> opt_and_plot.py ─┬─> struct_optimization.py ──> struct_analysis.py
 PB_Einfeld.py                   (rc_rib) ─┤                   ├─> struct_optimization_RCrib_cont.py
 TestAlgorithm.py                         ─┘                   ├─> class_to_excel_2.py
                                                                └─> class_to_excel.py   ⚠ only at ROOT today
 slab_2d_optimization.py (2D) ──> plot_datasets_2D.py ──> struct_optimization_2D.py ──> struct_analysis.py
                                         └─> class_to_excel_2.py
Data: database_260805.db, database_260811.db, 260625_slab_properties.db (opened by struct_analysis.Slab)
DB build: Database/Convert_Excel_to_DB.py -> database_260811.db ; Workflow/xlsx_to_db.py -> 260625_slab_properties.db
Post-processing: Workflow/Results/
```

**`class_to_excel.py` (the file PyCharm was finding):** `opt_and_plot.py` imports it, but it only exists at the repo root. It works today only because PyCharm puts the repo root on `sys.path`. → `git mv class_to_excel.py Workflow/`

**2D slab optimization stays in `Workflow/`.** It is the only 2D optimization in the active code. The other copies (root, `alt/Version 260126`, the Betonartikel snapshot) are older versions, and the `Workflow` versions are the newest (2026-08-05). What's wrong with them right now:
- `slab_2d_optimization.py:24` opens `database_260506_Hochbau.db`, which is not in `Workflow/`. The file exists in `Workflow/alt/`, at the root, and in the Betonartikel snapshot, so the run fails or creates an empty DB.
- That database has **the same tables and columns** as the current `database_260811.db` (`products`, `material_prop`, `floor_struc_prop`). It can be rebuilt with `Database/Convert_Excel_to_DB.py` from `260506_Datenbankdefinition_Hochbau_Stand210526.xlsx` (in `Database/alt/`). Alternatively, the 2D script could simply point at `database_260811.db`. That is a one-line change to suggest in the meeting, not part of this branch.
- Nobody has touched the 2D code since 2026-08-05, so it may not include later changes to `struct_analysis.py` (e.g. `Faktor_ger`, phi from the DB). It has to be test-run before anyone relies on it.

## Target structure
```
/
├── readme.md, .gitignore
├── Database/              Convert_Excel_to_DB.py, database_check.py, test_the_database.py,
│                          plot_products_NeueDB251030.py, database_260805.db
├── Workflow/              (flat; no alt/ folder anymore)
│   ├── struct_analysis.py, struct_optimization.py, struct_optimization_RCrib_cont.py, struct_optimization_2D.py
│   ├── opt_and_plot.py, plot_datasets_2D.py, class_to_excel.py (from root), class_to_excel_2.py
│   ├── 260513_simple_span_1d_Concrete.py, 260730_Anwendung_Timber.py, PB_Einfeld.py, TestAlgorithm.py, slab_2d_optimization.py
│   ├── xlsx_to_db.py, database_260805.db, database_260811.db, 260625_slab_properties.db
│   └── Results/           (unchanged, minus Results/alt)
└── archive/               (= renamed top-level alt/)
    ├── 250326-260121_databases/        old alt/*.db, products.csv, data.db, dummy_*.db
    ├── 260126_Version/                 old alt/Version 260126/
    ├── 260218_legacy_scripts/          old alt/*.py (Convert-csv-db, create_dummy_database, plot_CO2_sigma, plot_products, ungültig_test_rc)
    ├── 260513_Betonartikel_Copy/       whole folder moved unchanged (see below)
    ├── 260527_Test_Plots/              "Test Plots/"
    ├── 260730_Resultate/               root Resultate/
    ├── 260730_root_pipeline/           all root .py/.db except readme, .gitignore and class_to_excel.py
    ├── 260826_TestFiles/               TestFiles/ (incl. Concrete_Deflection)
    ├── 260903_Workflow_alt/            Workflow/alt/ (old struct_optimization versions + dbs incl. database_260506_Hochbau.db)
    ├── 260909_Workflow_Results_alt/    Workflow/Results/alt/
    ├── 260909_Database_old/            Database/alt/*, ModifyTables.py, plot_products.py, database_260304.db
    └── 261004_Workflow_superseded/
        ├── continuous_PB/              ContinuousSlab, opt_and_plotContPB (imports the missing struct_optimization_test), test_rc_rib_Continuous
        ├── material_statistics/        MaterialStatistics*.py, MatStatExtraction (open a missing database_260617_Hochbau.db)
        └── old_runs/                   260610_1D_Rc-Rec, Onewayslabs_hoa, struct_optimization_260903alt, test_rc_1D, test_rc_rib,
                                        test_slab, test_database, db_to_xlsx, slab_properties.db
```
Folder naming follows the repo's `YYMMDD_` convention. The date is the last commit that touched the contents (`git log -1 --format=%cs`). `test_*.py` are archived because they import `create_dummy_database`, `struct_optimization_test` and `plot_datasets`, none of which is in `Workflow/`.

**260513_Betonartikel_Copy:** a self-contained snapshot of `Workflow` from 2026-08-05: code, its own DBs, and `Results/260625_200_Iterationen` with the article figures. It moves as one block, untouched, so the figures stay next to the code version that produced them. Its inner `alt/` and `Results/` stay inside it.

## Steps (on the branch only; no commits, no push)
`git mv` stages each move, so when this is done all changes sit **staged, but not committed**, on `cleanup/archive`. `main` stays untouched.

0. `git checkout -b cleanup/archive` from clean `main`. Then run `git status --ignored --short` to make sure no local-only files would be left behind. Checked today: the output is empty and the working tree is clean.
1. `git mv alt archive`, then sort the existing contents into `250326-260121_databases/`, `260126_Version/` and `260218_legacy_scripts/`.
2. `git mv class_to_excel.py Workflow/`, then move the remaining root scripts and databases → `archive/260730_root_pipeline/`.
3. `git mv 260513_Betonartikel_Copy archive/`
4. `"Test Plots"` → `archive/260527_Test_Plots`, `TestFiles` → `archive/260826_TestFiles`, `Resultate` → `archive/260730_Resultate`
5. `git mv Workflow/alt archive/260903_Workflow_alt` and `git mv Workflow/Results/alt archive/260909_Workflow_Results_alt`
6. Old `Database/` files → `archive/260909_Database_old/`
7. Superseded `Workflow/` files → `archive/261004_Workflow_superseded/<group>/`
8. Leave the root `readme.md` and root `.gitignore` in place, unchanged. `Workflow/.gitignore` also stays as it is.
Nothing is committed or pushed.

Quote paths with spaces or umlauts (`"Test Plots"`, `"alt/Version 260126"`, `"alt/ungültig_test_rc.py"`).

## Verification (when the cleanup is carried out later)
- `git diff --cached -M --stat` shows only renames (R100), no content changes.
- `grep -nE "^\s*(import|from) " Workflow/*.py` shows that every imported local module exists in `Workflow/`.
- `cd Workflow && python -c "import struct_analysis, struct_optimization, opt_and_plot, plot_datasets_2D"` succeeds, run from a plain terminal and not PyCharm, so no root path is added.
- Run `TestAlgorithm.py` from `Workflow/` with a small `max_iter`. It should give the same result as on `main`.
- `git log main -1` is still 36ba32b.
