# Employee Exit Survey Analytics

[![CI](https://github.com/hari-qa-svg-development/employee-exit-survey-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/hari-qa-svg-development/employee-exit-survey-analytics/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-42a5f5)](https://github.com/astral-sh/ruff)

A reproducible **Python / Pandas** data-analytics project that cleans, transforms,
validates and analyzes employee exit-survey data from **DETE** and **TAFE** to
uncover *why* employees resign and *how* resignation patterns differ across
employee groups and institutes.

> The raw surveys are **synthetically generated** to faithfully reproduce the
> documented DETE/TAFE schema and real-world messiness (inconsistent headers,
> mixed date formats, categorical age/tenure, duplicate records, survey-specific
> "Contributing Factors" encodings). The full pipeline is deterministic and
> re-runnable end-to-end.

---

## What it does

| Stage | Module | Responsibility |
|-------|--------|----------------|
| **Load** | `src/load.py` | Import CSVs, profile shape / dtypes / missing values |
| **Clean** | `src/clean.py` | Standardize headers, drop noise, normalize missing markers, remove duplicates |
| **Transform** | `src/transform.py` | Dates → tenure, age midpoints & groups, tenure groups, dissatisfaction flag |
| **Validate** | `src/validate.py` | Required columns, domains, duplicates, missingness, vocabularies |
| **Combine** | `src/combine.py` | Unify schema, tag institute, concatenate DETE + TAFE |
| **Analyze** | `src/analyze.py` | Resignation reasons, DETE vs TAFE, dissatisfaction breakdowns, significance |
| **Visualize** | `src/visualize.py` | Charts for reasons, dissatisfaction, tenure, age, institute |

---

## Quick start

```bash
git clone https://github.com/hari-qa-svg-development/employee-exit-survey-analytics.git
cd employee-exit-survey-analytics
pip install -r requirements.txt

# 1. (Re)create the raw, messy survey datasets (seeded -> reproducible)
python scripts/generate_raw_data.py

# 2. Run the full pipeline: clean -> transform -> validate -> combine
#    -> analyze -> visualize -> report
python scripts/run_pipeline.py

# 3. Run the automated test suite
pytest
```

Outputs:

```
data/processed/combined_exit_survey.csv   # cleaned, analysis-ready dataset
reports/figures/*.png                     # visualizations
reports/business_insights.md              # final insights & HR recommendations
reports/run_summary.json                  # machine-readable run summary
notebooks/analysis.ipynb                  # interactive walkthrough
```

---

## Dissatisfaction business rule

- **DETE:** an employee is *dissatisfied* when **none** of the benign
  contributing factors (Career, Family, Maternity, None) was selected.
- **TAFE:** an employee is *dissatisfied* when the free-text contributing-factors
  field contains the token `"Dissatisfaction"`.

This is a documented, conservative proxy (blank/"None" factor sets are treated
as dissatisfaction). See *Limitations* in the report.

---

## Project layout

```
.
├── data/
│   ├── raw/                 # generated DETE & TAFE CSVs
│   └── processed/           # combined_exit_survey.csv
├── src/                     # pipeline modules (load, clean, transform, …)
├── tests/                   # pytest suite
├── notebooks/               # analysis.ipynb
├── reports/                 # business_insights.md + figures/
├── scripts/                 # data generation, pipeline, report
├── .github/workflows/ci.yml # continuous integration
├── pyproject.toml           # packaging & tool config
├── requirements.txt
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

---

## Testing

`pytest` covers the cleaning, transformation, validation and combination logic
with both hand-built fixtures and the real generated data:

```bash
pytest -q
# 29 passed
```

---

## Key findings (illustrative, synthetic data)

- ~58% of separations are voluntary resignations.
- Dissatisfaction among resignations is far higher at **DETE (~54%)** than
  **TAFE (~16%)**; the difference is statistically significant (χ² test).
- The dominant resignation reasons for both institutes are career-move factors,
  pointing to internal-mobility and career-development gaps.

See [`reports/business_insights.md`](reports/business_insights.md) for the full
narrative, charts and recommendations.

---

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup,
style and workflow.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).
