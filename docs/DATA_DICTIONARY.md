# Data Dictionary

Every field in the pipeline — raw inputs, cleaned intermediates, and the final
combined dataset — explained with its type, origin, allowed values and the
business rules that govern it.

Cross-references: [User Guide](USER_GUIDE.md) ·
[Pipeline Reference](PIPELINE_REFERENCE.md)

---

## Table of Contents

1. [Raw DETE fields](#raw-dete-fields)
2. [Raw TAFE fields](#raw-tafe-fields)
3. [Cleaned columns](#cleaned-columns)
4. [Final combined dataset](#final-combined-dataset)
5. [Business rules in detail](#business-rules-in-detail)
6. [Configurable thresholds](#configurable-thresholds)

---

## Raw DETE fields

Columns as they appear in `data/raw/dete_exit_survey.csv` (only a subset is
kept through cleaning — see `_DETE_KEEP` in `src/clean.py`).

| Raw column | Kept? | Description |
|------------|-------|-------------|
| `ID` | yes | Unique employee record identifier |
| `SeparationType` | yes | Reason employment ended (see allowed values below) |
| `Cease Date` | yes | Last day of employment — `YYYY/MM/DD` or `YYYY/MM` |
| `DETE Start Date` | yes | Date the employee started at DETE — `YYYY/MM/DD` or `YYYY/MM` |
| `Role Start Date` | no | Date the employee started in their current role |
| `Position` | no | Job title |
| `Classification` | no | Pay / seniority classification |
| `Region` | no | Work region |
| `Business Unit` | no | Organisational unit |
| `Employment Status` | yes | `Permanent` / `Temporary` / `Casual` / `Fixed Term` |
| `Career Move - Intent` | no | Whether the employee intended a career move (`Yes`/`No`) |
| `Career Move - Desire` | no | Whether the employee desired a career move |
| `Contributing Factors - Career` | yes | `Career Move"` if selected, else `"-"` |
| `Contributing Factors - Family` | yes | `"Maternity/Family"` if selected, else `"-"` |
| `Contributing Factors - Maternity` | yes | `"Maternity/Family"` if selected, else `"-"` |
| `Contributing Factors - None` | yes | `"None"` if selected, else `"-"` |
| `Professional Development` … `Rating - Staff Relations` | no | Opinion ratings (Agree/Neutral/Disagree or 1–5) |
| `Age` | yes | Age *range* string (see Age ranges below) |

### SeparationType allowed values

`Resignation`, `Resignation (Status Quo)`, `Resignation (Other)`,
`Retrenchment`, `Retirement`, `Transfer`, `Termination`, `Invalidity`, `Other`.

### Age ranges

`20 or younger`, `21-25`, `26-30`, `31-35`, `36-40`, `41-45`, `46-50`,
`51-55`, `56 or older`. Mapped to midpoints in `cfg.AGE_RANGE_MIDPOINTS`.

---

## Raw TAFE fields

Columns in `data/raw/tafe_survey.csv`.

| Raw column | Kept? | Description |
|------------|-------|-------------|
| `Record ID` | yes | Unique employee record identifier |
| `Institute` | yes | TAFE institute name (e.g. `Southbank`, `Brisbane`) |
| `WorkArea` | no | Functional work area |
| `CESSATION YEAR` | yes | Year employment ended (integer, may be missing) |
| `Reason for ceasing employment` | yes | Why employment ended (see below) |
| `Contributing Factors to Ceasing` | yes | `"; "`-joined list of selected factors |
| `Contributing Factors. <factor>` (×9) | yes | Individual factor flags (`Yes`/`No`) |
| `Gender` | yes | `Male` / `Female` / `Not Stated` |
| `Age` | yes | Age *range* string |
| `Employment Type` | yes | `Permanent` / `Temporary` / `Casual` / `Fixed Term` |
| `Current Length of Service` | yes | Tenure *category* (see below) |

### Reason for ceasing employment

`Resignation`, `Contract Expired`, `Retirement`, `Transfer`, `Other`,
`Termination of Employment`.

### Current Length of Service categories

`Less than 1`, `1-2`, `3-4`, `5-6`, `7-8`, `9-10`, `11-12`, `13-14`,
`15-16`, `17-18`, `19-20`, `More than 20`. Mapped to midpoints in
`cfg.LENGTH_OF_SERVICE_MIDPOINTS`.

---

## Cleaned columns

After `clean_dete` / `clean_tafe`, headers are snake_cased and only analysis
columns survive. Key normalized values:

| Situation | Normalized to |
|-----------|---------------|
| `"Not Stated"`, `""`, `" "`, `"nan"`, `"none"`, `"unknown"` | `NaN` |
| Blank DETE contributing-factor cell | `"-"` (means *not selected*) |
| TAFE factor flag `"Yes"/"True"/"1"` | `True` |
| TAFE factor flag `"No"/"False"/"0"` | `False` |
| TAFE factor flag missing | `pd.NA` |

---

## Final combined dataset

`data/processed/combined_exit_survey.csv` — the analysis-ready output.

| Column | Type | Origin | Description |
|--------|------|--------|-------------|
| `id` | `Int64` | DETE `ID` / TAFE `Record ID` | Employee record ID |
| `institute` | str | added by `combine` | Source survey: `DETE` or `TAFE` |
| `separation_type` | str | DETE `SeparationType` / TAFE `Reason for ceasing employment` | Why employment ended |
| `is_resignation` | bool | derived | `True` when `separation_type` contains `"resignation"` |
| `cease_year` | `Int64` | parsed from dates / `CESSATION YEAR` | Year employment ended |
| `age` | float | mapped from age-range string | Numeric age midpoint |
| `age_group` | str | derived | `<=30` / `31-40` / `41-50` / `51-60` / `>60` |
| `length_of_service` | float | DETE: `cease_year − start_year`; TAFE: category midpoint | Tenure in years |
| `tenure_group` | str | derived | `Less than 1` / `1-3` / `4-6` / `7-10` / `More than 10` |
| `employment_status` | str | DETE `Employment Status` / TAFE `Employment Type` | `Permanent` / `Temporary` / `Casual` / `Fixed Term` |
| `dissatisfied` | bool | derived | Dissatisfaction flag per business rule |
| `contributing_factors` | str | derived | `"; "`-joined reasons for leaving |

---

## Business rules in detail

### Resignation flag (`is_resignation`)

A row is a resignation when `separation_type` contains the substring
`"resignation"` (case-insensitive). This captures `Resignation`,
`Resignation (Status Quo)` and `Resignation (Other)` while excluding
`Retirement`, `Retrenchment`, `Transfer`, `Termination`, `Contract Expired`,
`Invalidity` and `Other`.

### Dissatisfaction flag (`dissatisfied`)

**DETE rule** — an employee is dissatisfied when **none** of the four benign
contributing factors was selected:

- `Contributing Factors - Career`
- `Contributing Factors - Family`
- `Contributing Factors - Maternity`
- `Contributing Factors - None`

Each column holds the factor name when selected, `"-"` when not. Selecting
*any* of them means the exit had a structural/benign explanation; selecting
*none* is treated as a dissatisfaction-driven resignation.

**TAFE rule** — an employee is dissatisfied when the combined
`Contributing Factors to Ceasing` field contains the token
`"Dissatisfaction"` (case-insensitive).

> **Assumption / limitation:** a blank or `"None"` factor set is interpreted
> as dissatisfaction. This is a documented, conservative proxy. Real surveys
> should capture an explicit satisfaction rating to remove the ambiguity.

### Tenure (`length_of_service`)

- **DETE:** `cease_year − dete_start_year`. Negative results (misordered dates)
  are set to NaN.
- **TAFE:** the categorical `Current Length of Service` is mapped to a numeric
  midpoint (e.g. `"1-2"` → `1.5`, `"More than 20"` → `22.0`).

### Age

Age arrives as a range string in both surveys. Each range is mapped to its
midpoint (e.g. `"31-35"` → `33`, `"56 or older"` → `58`). `"Not Stated"` and
other missing markers become NaN.

### Age groups

Cut from numeric `age` using `cfg.AGE_BINS = [0, 30, 40, 50, 60, 200]`:
`<=30`, `31-40`, `41-50`, `51-60`, `>60`.

### Tenure groups

Cut from numeric `length_of_service` using
`cfg.TENURE_BINS = [-0.01, 1, 3, 6, 10, 1000]`: `Less than 1`, `1-3`, `4-6`,
`7-10`, `More than 10`.

---

## Configurable thresholds

All guards live in `src/config.py` and can be tuned for new data:

| Threshold | Default | Controls |
|-----------|---------|----------|
| `VALID_CESSATION_YEARS` | `range(2009, 2019)` | Plausible cease-year window |
| `MIN_AGE` / `MAX_AGE` | `18` / `80` | Valid age range |
| `MIN_TENURE` / `MAX_TENURE` | `0` / `50` | Valid tenure range |
| `max_missing_pct` (in `validate`) | `25.0` | Max allowed NaN % on key fields |
| `RANDOM_SEED` | `42` | Synthetic data reproducibility |
