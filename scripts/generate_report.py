"""Generate the final business-insights report (``reports/business_insights.md``).

Numbers and charts are computed live from the combined dataset so the report is
always consistent with the data and the pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import src.analyze as az
import src.config as cfg
import src.validate as vd
from src.clean import clean_dete, clean_tafe
from src.combine import combine_datasets, filter_resignations
from src.load import load_dete, load_tafe
from src.transform import transform_dete, transform_tafe
from src.visualize import generate_all_figures


def _md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavored markdown table (no tabulate dep)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |"]
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def build() -> str:
    dete = transform_dete(clean_dete(load_dete())[0])
    tafe = transform_tafe(clean_tafe(load_tafe())[0])
    combined = combine_datasets(dete, tafe)
    res = filter_resignations(combined)

    summary = az.summarize(combined)
    comparison = az.compare_institutes(combined)
    reasons = az.top_resignation_reasons(combined)
    by_age = az.dissatisfaction_by_age(combined)
    by_tenure = az.dissatisfaction_by_tenure(combined)
    sig = az.significant_patterns(combined)
    figs = generate_all_figures(combined)

    rel = [Path(f).relative_to(cfg.REPORTS_DIR).as_posix() for f in figs]

    sig_rows = "\n".join(
        f"- **{r['variable']}**: chi2={r['chi2']}, p={r['p_value']} -> "
        f"{'significant' if r['significant'] else 'not significant'}"
        for r in sig.to_dict(orient="records")
    )

    significant_vars = ", ".join(
        r["variable"] for r in sig.to_dict(orient="records") if r["significant"]
    )

    dete_diss = summary["dete_dissatisfaction_rate_pct"]
    tafe_diss = summary["tafe_dissatisfaction_rate_pct"]

    md = f"""# Employee Exit Survey — Business Insights Report

*Generated automatically from the combined DETE + TAFE exit-survey dataset.*

## Executive Summary

- **{summary['total_records']:,}** survey records were cleaned, validated and combined
  ({cfg.DETE_LABEL} + {cfg.TAFE_LABEL}).
- **{summary['total_resignations']:,}** of those were voluntary **resignations**
  (**{summary['resignation_rate_pct']}%** of all separations).
- Overall **dissatisfaction rate among resignations: {summary['overall_dissatisfaction_rate_pct']}%**.
- Dissatisfaction differs sharply by institute: **{cfg.DETE_LABEL} = {dete_diss}%** vs
  **{cfg.TAFE_LABEL} = {tafe_diss}%**.
- Statistically significant drivers of dissatisfaction: **{significant_vars or 'none'}**.

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

- **{cfg.DETE_LABEL}:** an employee is *dissatisfied* when **none** of the benign
  contributing factors (Career, Family, Maternity, None) was selected.
- **{cfg.TAFE_LABEL}:** an employee is *dissatisfied* when the free-text
  contributing-factors field contains the token **"{cfg.TAFE_DISSATISFACTION_TOKEN}"**.

> Note: this is a documented, conservative proxy for dissatisfaction. In both
> surveys an empty/"None" factor set is interpreted as a dissatisfaction-driven
> exit. See *Limitations* below.

## Data Overview

| Metric | Value |
|---|---|
| Total records | {summary['total_records']:,} |
| Total resignations | {summary['total_resignations']:,} |
| Resignation rate | {summary['resignation_rate_pct']}% |
| Overall dissatisfaction (resignations) | {summary['overall_dissatisfaction_rate_pct']}% |
| Mean age (resignations) | {summary['mean_age']} |
| Mean tenure (resignations) | {summary['mean_tenure']} years |

## Key Findings

### 1. Top resignation reasons

{_md_table(reasons)}

![Top resignation reasons]({rel[0]})

### 2. DETE vs TAFE

{_md_table(comparison)}

![DETE vs TAFE comparison]({rel[4]})

The two institutes show materially different resignation profiles. {cfg.DETE_LABEL}
resignations carry a far higher dissatisfaction signal ({dete_diss}% vs {tafe_diss}%),
and {cfg.DETE_LABEL} leavers have longer average tenure
({comparison.loc[comparison['institute']==cfg.DETE_LABEL,'mean_tenure'].iloc[0]} yrs)
than {cfg.TAFE_LABEL}
({comparison.loc[comparison['institute']==cfg.TAFE_LABEL,'mean_tenure'].iloc[0]} yrs).
This suggests {cfg.DETE_LABEL} is losing *tenured, disengaged* staff, whereas
{cfg.TAFE_LABEL} exits are more often proactive career moves.

### 3. Dissatisfaction by age

{_md_table(by_age)}

![Dissatisfaction by age]({rel[2]})

### 4. Dissatisfaction by tenure

{_md_table(by_tenure)}

![Dissatisfaction by tenure]({rel[3]})

![Dissatisfaction by institute]({rel[1]})

## Significant Patterns (Chi-square)

{sig_rows}

## HR Recommendations

1. **Target {cfg.DETE_LABEL} retention first.** With a ~{dete_diss}% dissatisfaction
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
"""
    return md


def main() -> None:
    cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md = build()
    out = cfg.REPORTS_DIR / "business_insights.md"
    out.write_text(md)
    print(f"Wrote {out} ({len(md)} chars)")


if __name__ == "__main__":
    main()
