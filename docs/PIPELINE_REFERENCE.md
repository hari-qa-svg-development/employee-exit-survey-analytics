# Pipeline Reference

A detailed, function-by-function reference for every module in `src/`. Use this
to understand, modify, or extend the pipeline. For *how to run* things, see the
[User Guide](USER_GUIDE.md); for *what each field means*, see the
[Data Dictionary](DATA_DICTIONARY.md).

---

## Table of Contents

1. [src/config.py — shared configuration](#srcconfigpy)
2. [src/load.py — load & profile](#srcloadpy)
3. [src/clean.py — clean](#srccleanpy)
4. [src/transform.py — transform](#srctransformpy)
5. [src/combine.py — combine](#srccombinepy)
6. [src/validate.py — validate](#srcvalidatepy)
7. [src/analyze.py — analyze](#srcanalyzepy)
8. [src/visualize.py — visualize](#srcvisualizepy)
9. [Data flow summary](#data-flow-summary)

---

## `src/config.py`

Single source of truth for every magic string, threshold and path. Edit here to
adapt the pipeline to new data without touching business logic.

| Constant | Type | Purpose |
|----------|------|---------|
| `PROJECT_ROOT`, `DATA_RAW`, `DATA_PROCESSED`, `REPORTS_DIR`, `FIGURES_DIR` | `Path` | Filesystem layout |
| `DETE_RAW_PATH`, `TAFE_RAW_PATH`, `COMBINED_PATH` | `Path` | Key artifact locations |
| `DETE_LABEL`, `TAFE_LABEL` | `str` | Institute tags (`"DETE"` / `"TAFE"`) |
| `RESIGNATION_KEYWORDS` | tuple | Substrings that mark a resignation |
| `DETE_CONTRIBUTING_FACTORS` | list | The four factor columns driving the DETE rule |
| `DETE_NOT_SELECTED_TOKEN` | `str` | `"-"` — means a DETE factor was not selected |
| `TAFE_DISSATISFACTION_TOKEN` | `str` | `"Dissatisfaction"` — token in TAFE's combined field |
| `TAFE_INDIVIDUAL_FACTORS` | list | (column, label) pairs for TAFE factor flags |
| `AGE_BINS`, `AGE_LABELS` | list | Age-group bin edges and labels |
| `AGE_RANGE_MIDPOINTS` | dict | Maps age-range string → numeric midpoint |
| `TENURE_BINS`, `TENURE_LABELS` | list | Tenure-group bin edges and labels |
| `LENGTH_OF_SERVICE_MIDPOINTS` | dict | Maps TAFE length-of-service category → years |
| `VALID_CESSATION_YEARS` | range | Plausible survey window (validation guard) |
| `MIN_AGE`, `MAX_AGE`, `MIN_TENURE`, `MAX_TENURE` | int/float | Validation guards |
| `COMBINED_REQUIRED_COLUMNS` | list | Columns that must exist post-combine |
| `RANDOM_SEED` | `int` | Seed for the synthetic data generator |

---

## `src/load.py`

IO layer. Keeps CSV reading in one place and provides a quick profile.

### `load_dete(path=cfg.DETE_RAW_PATH) -> pd.DataFrame`
Reads the raw DETE survey with `dtype=str` so nothing is coerced prematurely.
Missing values are kept as real NaN (`keep_default_na=True`).

### `load_tafe(path=cfg.TAFE_RAW_PATH) -> pd.DataFrame`
Same contract as `load_dete` for the TAFE survey.

### `profile(df) -> pd.DataFrame`
Returns a per-column summary DataFrame with: `dtype`, `non_null`, `missing`,
`missing_pct`, `n_unique`. Use it to spot-check a new dataset before cleaning.

### `profile_pair(dete, tafe) -> dict`
Convenience wrapper that profiles both datasets and returns shapes, column
lists and profiles in one dict (used by the notebook).

---

## `src/clean.py`

All cleaning logic. The public functions return `(cleaned_df, report_dict)` so
callers can audit what changed.

### `standardize_columns(df) -> pd.DataFrame`
Snake-cases every header: lowercases, strips, replaces `(`, `)`, `/`, `.`, `-`
with spaces, collapses runs of whitespace to a single `_`. E.g.
`" CESSATION YEAR "` → `"cessation_year"`.

### `_std(name) -> str`
The single-column version of the above (used internally and in tests).

### `_normalize_missing(df) -> pd.DataFrame`
Replaces common null-ish tokens (`""`, `" "`, `"nan"`, `"na"`, `"none"`,
`"not stated"`, `"notstated"`, `"unknown"`) with real `float("nan")` on every
non-numeric column.

### `drop_duplicates(df) -> (pd.DataFrame, int)`
Drops exact duplicate rows, resets the index, and returns the cleaned frame plus
the count of rows removed.

### `_keep_subset(df, raw_keep) -> pd.DataFrame`
Filters columns to the whitelist (`_DETE_KEEP` or `_TAFE_KEEP`). Anything not in
the whitelist is treated as irrelevant noise and dropped.

### `clean_dete(df) -> (pd.DataFrame, dict)`
Full DETE cleaning pipeline:
1. standardize columns
2. keep only `_DETE_KEEP` columns
3. normalize missing markers
4. fill the four contributing-factor columns' blanks with `"-"` (not-selected)
5. drop duplicates

Report keys: `columns_after_standardize`, `dropped_columns`,
`duplicates_dropped`, `rows_after`.

### `clean_tafe(df) -> (pd.DataFrame, dict)`
Full TAFE cleaning pipeline:
1. standardize columns
2. keep only `_TAFE_KEEP` columns
3. normalize missing markers
4. map the individual contributing-factor flags (`"Yes"/"No"`) to booleans
5. drop duplicates

---

## `src/transform.py`

Converts cleaned frames into the unified analysis schema.

### `extract_year(series) -> pd.Series`
Pulls the first 4-digit year out of messy date strings via regex
`(\d{4})`. Handles both `YYYY/MM/DD` and `YYYY/MM`. Non-matches → NaN.

### `dete_tenure(cease_year, start_year) -> pd.Series`
`cease_year − start_year`; negative results are set to NaN (guards against
misordered dates).

### `map_age_ranges(series) -> pd.Series`
Maps an age-range string (e.g. `"31-35"`) to its numeric midpoint using
`cfg.AGE_RANGE_MIDPOINTS`. Unknown strings → NaN.

### `add_age_group(df, age_col="age") -> pd.DataFrame`
Adds an `age_group` column by cutting `age` into `cfg.AGE_BINS` with
`cfg.AGE_LABELS`.

### `map_length_of_service(series) -> pd.Series`
Maps TAFE's categorical length-of-service (e.g. `"1-2"`) to a numeric midpoint
using `cfg.LENGTH_OF_SERVICE_MIDPOINTS`.

### `add_tenure_group(df, tenure_col="length_of_service") -> pd.DataFrame`
Adds a `tenure_group` column by cutting tenure into `cfg.TENURE_BINS` with
`cfg.TENURE_LABELS`.

### `flag_dissatisfied_dete(df) -> pd.Series`
**Business rule (DETE):** `True` when *none* of the four benign contributing
factors (Career, Family, Maternity, None) was selected. Each factor column
holds the factor name when selected, `"-"` when not.

### `flag_dissatisfied_tafe(df) -> pd.Series`
**Business rule (TAFE):** `True` when the combined `contributing_factors_to_ceasing`
field contains the token `"Dissatisfaction"` (case-insensitive).

### `build_contributing_factors_dete(df) -> pd.Series`
Reconstructs DETE's selected factors as a `"; "`-joined string (e.g.
`"Career Move; Maternity/Family"`). Used so DETE and TAFE share one
`contributing_factors` column.

### `transform_dete(df) -> pd.DataFrame`
Runs the full DETE transform: parse dates → `cease_year` + `length_of_service`,
map age, flag dissatisfaction, build `contributing_factors`, add groups.

### `transform_tafe(df) -> pd.DataFrame`
Runs the full TAFE transform: coerce `cease_year`, map length-of-service and age,
flag dissatisfaction, copy the combined factors field, add groups.

---

## `src/combine.py`

### `_finalize(df, institute) -> pd.DataFrame`
Tags a frame with its `institute` label and derives `is_resignation` by checking
whether `separation_type` contains `"resignation"` (case-insensitive).

### `combine_datasets(dete, tafe) -> pd.DataFrame`
Finalizes both frames, keeps only the shared analysis columns, and concatenates
them with a reset index. Output columns:

```
id, institute, separation_type, is_resignation, cease_year, age, age_group,
length_of_service, tenure_group, employment_status, dissatisfied, contributing_factors
```

### `filter_resignations(df) -> pd.DataFrame`
Returns only rows where `is_resignation == True`. Most analysis functions call
this internally.

---

## `src/validate.py`

### `ValidationError`
Exception raised when any check fails.

### `ValidationReport`
Dataclass holding a list of `{check, passed, detail}` dicts. `__str__` renders a
`[PASS]`/`[FAIL]` report. `passed` is `True` only if every check passed.

### `validate(df, max_missing_pct=25.0) -> ValidationReport`
Runs the full suite and raises `ValidationError` if anything fails:

1. **required columns** — all `cfg.COMBINED_REQUIRED_COLUMNS` present
2. **domains** — `cease_year` in range, `age` and `tenure` within guards,
   `dissatisfied` is boolean
3. **duplicates** — no fully-duplicate rows
4. **missingness** — `separation_type`, `institute`, `is_resignation`,
   `dissatisfied` each ≤ `max_missing_pct` NaN
5. **vocabularies** — `institute` ∈ {DETE, TAFE}; `is_resignation` is boolean

---

## `src/analyze.py`

All functions are pure (DataFrame in → DataFrame/dict out).

### `_explode_factors(df) -> pd.DataFrame`
Splits the `"; "`-joined `contributing_factors` into one row per factor. Used by
all reason-frequency functions.

### `top_resignation_reasons(df, top_n=10) -> pd.DataFrame`
Factor frequency among resignations. Columns: `factor`, `count`.

### `reasons_by_institute(df) -> pd.DataFrame`
Per-institute factor share (percentage of that institute's resignations that
mention each factor). Columns: `institute`, `factor`, `pct`.

### `compare_institutes(df) -> pd.DataFrame`
Side-by-side summary per institute: `n_resignations`, `dissatisfaction_rate`,
`mean_age`, `mean_tenure`, `pct_permanent`.

### `dissatisfaction_by(df, group_col) -> pd.DataFrame`
Generic grouped dissatisfaction table: `n`, `dissatisfied` (count),
`dissatisfaction_rate_pct`.

### `dissatisfaction_by_age`, `..._by_tenure`, `..._by_institute`
Thin wrappers over `dissatisfaction_by` for the common dimensions.

### `_chi2(df, var) -> dict`
Chi-square test of independence between `var` and `dissatisfaction` using
`scipy.stats.chi2_contingency`. Returns `variable`, `chi2`, `p_value`, `dof`,
`significant` (p < 0.05). Returns NaN stats when the contingency table is too
small.

### `significant_patterns(df) -> pd.DataFrame`
Runs `_chi2` against `institute`, `age_group`, `tenure_group`,
`employment_status`.

### `summarize(df) -> dict`
Headline numbers: `total_records`, `total_resignations`,
`resignation_rate_pct`, overall / per-institute dissatisfaction rates,
`mean_age`, `mean_tenure`.

---

## `src/visualize.py`

Uses `matplotlib` + `seaborn` in headless mode (`matplotlib.use("Agg")`), so it
runs on servers/CI without a display.

| Function | Chart |
|----------|-------|
| `plot_top_reasons(df)` | Horizontal bar — top contributing factors |
| `plot_dissatisfaction_by_institute(df)` | Bar — dissatisfaction % per institute |
| `plot_dissatisfaction_by_age(df)` | Bar — dissatisfaction % per age group |
| `plot_dissatisfaction_by_tenure(df)` | Bar — dissatisfaction % per tenure group |
| `plot_institute_comparison(df)` | Grouped bars — dissatisfaction % vs permanent % |
| `generate_all_figures(df, outdir=None)` | Runs all five, returns list of PNG paths |

Each `plot_*` function accepts an optional `path` override and returns the file
path written. Colors use `PALETTE = {"DETE": "#2c7fb8", "TAFE": "#d95f0e"}`.

---

## Data flow summary

```
dete_exit_survey.csv ──► load_dete() ──► clean_dete() ──► transform_dete() ─┐
                                                                            ├► combine_datasets() ──► validate() ──► analyze / visualize / report
tafe_survey.csv    ──► load_tafe() ──► clean_tafe() ──► transform_tafe() ─┘
```

`scripts/run_pipeline.py` wires these together, writes
`data/processed/combined_exit_survey.csv`, the figures, and
`reports/business_insights.md`. `scripts/generate_report.py` builds the report
from live results so numbers always match the data.
