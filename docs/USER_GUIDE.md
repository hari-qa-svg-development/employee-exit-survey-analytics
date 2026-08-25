# User Guide

Complete setup, installation, and usage guide for the Employee Exit Survey
Analytics project.

---

## Table of Contents

1. [Who this is for](#who-this-is-for)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Quick-start walkthrough](#quick-start-walkthrough)
5. [Understanding the outputs](#understanding-the-outputs)
6. [Running individual stages](#running-individual-stages)
7. [Using the notebook](#using-the-notebook)
8. [Daily automated email report](#daily-automated-email-report)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Who this is for

- **Data analysts / data engineers** learning real-world data cleaning with Pandas.
- **HR / People-Analytics teams** who want a reproducible exit-survey analysis
  template they can adapt to their own data.
- **Students / job-seekers** building a portfolio project that demonstrates the
  full analytics workflow: load → clean → transform → validate → combine →
  analyze → visualize → report.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.10 or newer (3.10–3.13 tested in CI) |
| OS | macOS, Linux, or Windows (WSL recommended) |
| RAM | 4 GB minimum |
| Disk | ~50 MB for the repo; generated artifacts are small |
| Git | Any recent version |

No prior Pandas expertise is required — the code is commented via docstrings and
the [Pipeline Reference](PIPELINE_REFERENCE.md) explains every function.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/hari-qa-svg-development/employee-exit-survey-analytics.git
cd employee-exit-survey-analytics
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Core dependencies and why they are used:

| Package    | Purpose                                            |
|------------|----------------------------------------------------|
| `pandas`   | DataFrames, I/O, transformations                   |
| `numpy`    | Numeric operations, NaN handling                   |
| `matplotlib` | Base plotting                                    |
| `seaborn`  | Statistical visualizations (used by `visualize.py`) |
| `scipy`    | Chi-square tests (`analyze.py` significance checks) |
| `pytest`   | Test framework                                     |

---

## Quick-start walkthrough

Three commands take you from a fresh clone to a full analysis:

```bash
# Step 1 — generate the raw, messy survey datasets
# (seeded with RANDOM_SEED=42 so results are reproducible)
python scripts/generate_raw_data.py

# Step 2 — run the entire pipeline end-to-end
python scripts/run_pipeline.py

# Step 3 — run the automated test suite
pytest
```

Expected console output (abbreviated):

```
1/7  Loading raw surveys ...
2/7  Cleaning ...
3/7  Transforming ...
4/7  Combining ...
5/7  Validating ...
[PASS] required_columns missing=[]
[PASS] cease_year_domain 0 out-of-range
...
6/7  Analyzing ...
7/7  Visualizing ...
+     Generating business insights report ...
Wrote combined dataset -> data/processed/combined_exit_survey.csv
Run summary: { "total_records": 1100, "total_resignations": 635, ... }
```

---

## Understanding the outputs

After `run_pipeline.py` finishes, your project tree contains:

```
data/
  raw/
    dete_exit_survey.csv           # generated raw DETE survey (~615 rows)
    tafe_survey.csv                # generated raw TAFE survey (~512 rows)
  processed/
    combined_exit_survey.csv       # cleaned, unified dataset (1,100 rows)
reports/
  business_insights.md             # narrative report with findings + recommendations
  run_summary.json                 # machine-readable summary of this run
  figures/
    top_resignation_reasons.png
    dissatisfaction_by_institute.png
    dissatisfaction_by_age.png
    dissatisfaction_by_tenure.png
    institute_comparison.png
```

### `combined_exit_survey.csv` columns

| Column               | Type    | Description                                              |
|----------------------|---------|----------------------------------------------------------|
| `id`         | int     | Employee record ID                                       |
| `institute`  | str     | Source survey: `DETE` or `TAFE`                          |
| `separation_type`    | str     | Why the employee left (e.g. Resignation, Retirement)     |
| `is_resignation`    | bool    | `True` for voluntary resignations                        |
| `cease_year` | int     | Year employment ended                                    |
| `age`        | float   | Employee age as a numeric midpoint                       |
| `age_group`  | str     | Bucketed age: `<=30`, `31-40`, `41-50`, `51-60`, `>60`   |
| `length_of_service`  | float   | Tenure in years                                          |
| `tenure_group`      | str     | Bucketed tenure (see Data Dictionary)                    |
| `employment_status`  | str     | Permanent / Temporary / Casual / Fixed Term              |
| `dissatisfied`       | bool    | Dissatisfaction flag per the business rule               |
| `contributing_factors`| str    | Semicolon-separated reasons for leaving                  |

### `run_summary.json`

A machine-readable snapshot produced every run. Useful for dashboards or
change-detection. Keys include `total_records`, `total_resignations`,
`resignation_rate_pct`, `overall_dissatisfaction_rate_pct`, per-institute
dissatisfaction rates, and the results of every chi-square test.

---

## Running individual stages

You don't always need the full pipeline. Each stage is a standalone Python
module you can run directly, and the functions are importable.

### Load + profile only

```python
from src.load import load_dete, load_tafe, profile

dete = load_dete()
print(profile(dete))
```

### Clean only

```python
from src.load import load_dete
from src.clean import clean_dete

dete_clean, report = clean_dete(load_dete())
print("Duplicates dropped:", report["duplicates_dropped"])
print("Columns dropped:", report["dropped_columns"])
```

### Transform only

```python
from src.clean import clean_dete
from src.transform import transform_dete

df = transform_dete(clean_dete(load_dete())[0])
print(df[["id", "age", "length_of_service", "dissatisfied"]].head())
```

### Validate only

```python
from src.validate import validate
# `validate` returns a report; it raises ValidationError on failure
report = validate(my_dataframe)
print(report)
```

### Analyze / visualize directly

```python
import src.analyze as az
import src.visualize as vz

print(az.summarize(combined))
az.top_resignation_reasons(combined)
vz.plot_dissatisfaction_by_age(combined)
```

Run any module as a script for a quick demo:

```bash
python -m src.load
python -m src.clean
python -m src.transform
python -m src.combine
python -m src.validate
python -m src.analyze
python -m src.visualize
```

---

## Using the notebook

`notebooks/analysis.ipynb` mirrors the pipeline interactively with rendered
tables and charts.

```bash
pip install jupyter     # if not already installed
jupyter notebook notebooks/analysis.ipynb
```

The notebook:
1. Imports the pipeline modules from `src/`.
2. Runs each stage and prints intermediate results.
3. Displays the generated figures inline (`IPython.display.Image`).

> Tip: use it to experiment. Edit a transform, re-run the cell, and see how
> the outputs change before committing the change back to the module.

---

## Daily automated email report

The repo ships a scheduled GitHub Actions workflow
(`.github/workflows/daily_report.yml`) that:

1. Runs the **entire pipeline** every day at **05:00 IST** (23:30 UTC).
2. Builds a **styled HTML email** from the insights report
   (`scripts/build_email.py`) with the charts embedded inline.
3. Sends it via SMTP (`scripts/send_email.py`).

### Configure the secrets

In **Settings → Secrets and variables → Actions** on GitHub, add:

| Secret | Example |
|--------|---------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your login / sending address |
| `SMTP_PASS` | app password (not your normal password) |
| `EMAIL_FROM` | the sender address |
| `EMAIL_TO` | comma-separated recipients, e.g. `hr@company.com, boss@company.com` |

> For Gmail, enable **2-Step Verification** and create an **App Password**
> (https://myaccount.google.com/apppasswords); use that as `SMTP_PASS`.

### Trigger it

- **Automatic:** runs daily at 05:00 IST. (GitHub may delay scheduled runs on
  repos with no activity for 60+ days.)
- **Manual:** `Actions → Daily Exit-Survey Report → Run workflow`, or push a
  commit.

### Run locally (e.g. to preview)

```bash
python scripts/run_pipeline.py
python scripts/build_email.py
SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USER=you@gmail.com \
SMTP_PASS=app-pass EMAIL_FROM=you@gmail.com EMAIL_TO=boss@company.com \
python scripts/send_email.py            # actually sends

# or preview without sending:
python scripts/send_email.py --dry-run
```

### Notes

- The default schedule is 05:00 **IST** (`30 23 * * *` UTC). Edit the `cron:`
  line to change the time or use a different timezone.
- The raw data is **synthetic and reproducible** (fixed seed). The email will
  look the same each day until you plug in real surveys (see the
  [Data Dictionary](DATA_DICTIONARY.md) for wiring your own files).

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'src'`

Run scripts from the **project root**, or use the entrypoint form
(`python -m src.load`). The notebook adds the parent folder to `sys.path`.

### `ModuleNotFoundError` for pandas / numpy / etc.

You forgot to install dependencies or activate the virtual environment:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Validation fails with `out-of-range` years or ages

If you plug in your own real data, edit the guards in `src/config.py`:

```python
VALID_CESSATION_YEARS = range(2009, 2019)
MIN_AGE = 18
MAX_AGE = 80
```

### `gh` / push issues

See the repo README — authentication uses `gh auth login`.

### Tests fail on date parsing

The DETE `cease_date` field accepts both `YYYY/MM/DD` and `YYYY/MM`. If your
real data uses a different format, adjust `extract_year()` in
`src/transform.py`.

---

## FAQ

**Q: Is this real data?**  
A: The raw CSVs are *synthetic* — generated to mirror the documented DETE/TAFE
structure and messiness. Swap in real surveys at `data/raw/` and the pipeline
runs unchanged.

**Q: How do I use my own data?**  
A: Replace `data/raw/dete_exit_survey.csv` and `data/raw/tafe_survey.csv` with
your files (keeping a compatible shape), or wire new sources into `src/load.py`
and adjust the column mapping in `src/clean.py`.

**Q: Can I change the dissatisfaction rule?**  
A: Yes. Edit `flag_dissatisfied_dete` / `flag_dissatisfied_tafe` in
`src/transform.py`. The [Data Dictionary](DATA_DICTIONARY.md) explains the rule
and its assumptions.

**Q: How is tenure calculated?**  
A: DETE: `cease_year − start_year`. TAFE: categorical length-of-service mapped
to midpoints (see `LENGTH_OF_SERVICE_MIDPOINTS` in `src/config.py`).

**Q: Where do I add a new chart?**  
A: Add a function in `src/visualize.py` and call it from
`generate_all_figures()`. Add a test in `tests/` if it encapsulates logic.
