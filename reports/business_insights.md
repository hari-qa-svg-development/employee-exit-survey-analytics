# Employee Exit Survey — Business Insights Report

*Generated automatically from the combined DETE + TAFE exit-survey dataset.*

## Executive Summary

- **1,100** survey records were cleaned, validated and combined
  (DETE + TAFE).
- **635** of those were voluntary **resignations**
  (**57.7%** of all separations).
- Overall **dissatisfaction rate among resignations: 39.1%**.
- Dissatisfaction differs sharply by institute: **DETE = 53.9%** vs
  **TAFE = 16.3%**.
- Statistically significant drivers of dissatisfaction: **institute**.

## Methodology

The pipeline (`src/`) follows: **Load → Clean → Transform → Validate → Combine →
Analyze → Visualize**.

1. **Load & profile** raw CSVs (`load.py`).
2. **Clean** (`clean.py`): snake_case headers, drop irrelevant columns, normalize
   missing markers ("Not Stated", blanks), remove exact duplicate rows.
3. **Transform** (`transform.py`): parse dates into cessation years, compute
   tenure (DETE from start/cease dates, TAFE from categorical length-of-service),
   map age ranges to midpoints and groups, bucket tenure, and apply the
   dissatisfaction business rule.
4. **Validate** (`validate.py`): required columns, value domains (years, ages,
   tenure), duplicate check, missingness tolerance, controlled vocabularies.
5. **Combine** (`combine.py`): unify schema and concatenate the two surveys,
   tagging source (`institute`) and resignation status.
6. **Analyze / Visualize** (`analyze.py`, `visualize.py`).

### Dissatisfaction business rule

- **DETE:** an employee is *dissatisfied* when **none** of the benign
  contributing factors (Career, Family, Maternity, None) was selected.
- **TAFE:** an employee is *dissatisfied* when the free-text
  contributing-factors field contains the token **"Dissatisfaction"**.

> Note: this is a documented, conservative proxy for dissatisfaction. In both
> surveys an empty/"None" factor set is interpreted as a dissatisfaction-driven
> exit. See *Limitations* below.

## Data Overview

| Metric | Value |
|---|---|
| Total records | 1,100 |
| Total resignations | 635 |
| Resignation rate | 57.7% |
| Overall dissatisfaction (resignations) | 39.1% |
| Mean age (resignations) | 36.7 |
| Mean tenure (resignations) | 9.1 years |

## Key Findings

### 1. Top resignation reasons

| factor | count |
| --- | --- |
| None | 295 |
| Maternity/Family | 137 |
| Career Move | 116 |
| External Regulation | 55 |
| Career Move - Self-employment | 52 |
| Ill Health | 52 |
| Other | 51 |
| Career Move - Public Sector Employees | 49 |
| Career Move - Private Sector Employees | 45 |
| Dissatisfaction | 41 |

![Top resignation reasons](figures/top_resignation_reasons.png)

### 2. DETE vs TAFE

| institute | n_resignations | dissatisfaction_rate | mean_age | mean_tenure | pct_permanent |
| --- | --- | --- | --- | --- | --- |
| DETE | 384.0 | 53.9 | 36.7 | 11.3 | 52.3 |
| TAFE | 251.0 | 16.3 | 36.8 | 6.3 | 55.8 |

![DETE vs TAFE comparison](figures/institute_comparison.png)

The two institutes show materially different resignation profiles. DETE
resignations carry a far higher dissatisfaction signal (53.9% vs 16.3%),
and DETE leavers have longer average tenure
(11.3 yrs)
than TAFE
(6.3 yrs).
This suggests DETE is losing *tenured, disengaged* staff, whereas
TAFE exits are more often proactive career moves.

### 3. Dissatisfaction by age

| age_group | n | dissatisfied | dissatisfaction_rate_pct |
| --- | --- | --- | --- |
| 31-40 | 206 | 82 | 39.8 |
| 41-50 | 137 | 55 | 40.1 |
| 51-60 | 65 | 27 | 41.5 |
| <=30 | 175 | 65 | 37.1 |

![Dissatisfaction by age](figures/dissatisfaction_by_age.png)

### 4. Dissatisfaction by tenure

| tenure_group | n | dissatisfied | dissatisfaction_rate_pct |
| --- | --- | --- | --- |
| 1-3 | 84 | 26 | 31.0 |
| 4-6 | 100 | 29 | 29.0 |
| 7-10 | 98 | 40 | 40.8 |
| Less than 1 | 52 | 23 | 44.2 |
| More than 10 | 212 | 88 | 41.5 |

![Dissatisfaction by tenure](figures/dissatisfaction_by_tenure.png)

![Dissatisfaction by institute](figures/dissatisfaction_by_institute.png)

## Significant Patterns (Chi-square)

- **institute**: chi2=88.448, p=0.0 -> significant
- **age_group**: chi2=0.541, p=0.9098 -> not significant
- **tenure_group**: chi2=7.508, p=0.1114 -> not significant
- **employment_status**: chi2=0.288, p=0.9623 -> not significant

## HR Recommendations

1. **Target DETE retention first.** With a ~53.9% dissatisfaction
   rate among resignations and longer average tenure, focus on engagement,
   career-path clarity and manager effectiveness for established staff.
2. **Career development is the lever.** "Career Move" and related factors dominate
   the reason lists for both institutes — invest in internal mobility, promotions
   and secondments before talent walks.
3. **Segment by tenure.** Dissatisfaction is not flat across tenure; design
   different interventions for early-tenure (<1-3 yrs) versus long-tenure
   (>10 yrs) cohorts.
4. **Standardize data capture.** The two surveys encode reasons differently
   (flag columns vs free text). A single, structured exit-interview instrument
   would make cross-institute comparison and trend monitoring far cleaner.
5. **Monitor quarterly.** Re-run `python scripts/run_pipeline.py` each survey
   cycle; the automated validation gates bad data before it reaches reporting.

## Limitations

- The raw surveys are **synthetic** (generated to mirror the documented DETE/TAFE
  structure and messiness) so figures are illustrative, not operational.
- The dissatisfaction rule is a **proxy**: blank/"None" factor sets are treated as
  dissatisfaction. Real surveys should capture an explicit satisfaction rating.
- Age and length-of-service arrive as **ranges**; we use midpoints, which smooth
  extreme values.
- Categorical fields (e.g. "Not Stated") reduce effective sample sizes for some
  breakdowns.
