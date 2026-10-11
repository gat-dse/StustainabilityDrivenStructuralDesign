# Code for Project "Nachhaltigkeit im Tragwerksentwurf"
kfm research group, ibk, ETHZ

## Setup
Python 3.14 (python.org installer). Install the packages into a local environment:
```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
In PyCharm, select `.venv/bin/python` as the project interpreter (Settings → Project → Python Interpreter → Add → Existing).

Requirements: numpy, scipy, pandas, openpyxl, matplotlib, seaborn, shapely, optuna (versions in `requirements.txt`).
Run scripts from inside `Workflow/`, because the databases are opened by relative path.
