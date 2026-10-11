# Handoff – repo cleanup (2026-10-04)

State: nothing changed yet. `main` is clean at `36ba32b`. The full cleanup plan is in `HANDOFF_CLEANUPPLAN.md`.

## Next steps
1. Discuss the cleanup plan with the supervisor: keep the `Workflow/` pipeline flat, and move everything else into a dated `archive/` (the renamed top-level `alt/`).
2. If approved: create the branch `cleanup/archive` from `main` and carry out the moves with `git mv`.
3. Review with `git diff --cached -M --stat` (it should show only renames), then commit, push the branch and open a draft PR.
4. Point `Workflow/slab_2d_optimization.py` at `database_260811.db` (it has the same tables as `database_260506_Hochbau.db`) and test-run the 2D pipeline.
5. Get `260811_Datenbankdefinition.xlsx` into the repo: force-add it, or add a `!Database/*.xlsx` exception to `.gitignore`.
6. Later: add a central `paths.py` for database paths, like the other thesis (`core/paths.py`).
7. Later: port the missing slab types from the other thesis: post-tensioned concrete (`pc_rec`), timber-concrete composite (`tcc`), punching shear, and the acoustic floor build-up.

## Open issues
- `Workflow/opt_and_plot.py` imports `class_to_excel.py`, which only exists at the repo root. It works only through PyCharm adding the root to `sys.path`.
- `Workflow/slab_2d_optimization.py` opens `database_260506_Hochbau.db`, which is not in `Workflow/` (only in `Workflow/alt/`, the root, and the Betonartikel copy).
- `Database/Convert_Excel_to_DB.py` needs `260811_Datenbankdefinition.xlsx`, which is not in the repo or on disk.
- Several `Workflow/` scripts open databases that are in the wrong folder or don't exist: `database_260610_Hochbau.db`, `database_260617_Hochbau.db`, `database_260506_Hochbau.db`.
- There are 5 diverging copies of `struct_analysis.py`. `Workflow/struct_analysis.py` is the current one.
- The 2D code (`slab_2d_optimization.py`, `plot_datasets_2D.py`, `struct_optimization_2D.py`) was last changed on 2026-08-05 and has not been tested against the current `struct_analysis.py`.
