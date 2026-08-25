"""Analyze the combined exit-survey dataset.

Functions here are pure (take a DataFrame, return a DataFrame/dict) so the
notebook, the report generator and the tests can all reuse them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import src.config as cfg


# --------------------------------------------------------------------------- #
# Resignation reasons
# --------------------------------------------------------------------------- #
def _explode_factors(df: pd.DataFrame) -> pd.DataFrame:
    """Explode the '; '-joined contributing_factors into one row per factor."""
    tmp = df.copy()
    tmp["factor"] = tmp["contributing_factors"].astype(str).str.split("; ")
    return tmp.explode("factor").reset_index(drop=True)


def top_resignation_reasons(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Frequency of each contributing factor among resignations."""
    res = df[df["is_resignation"]].copy()
    exploded = _explode_factors(res)
    counts = exploded["factor"].value_counts().head(top_n)
    return counts.rename_axis("factor").reset_index(name="count")


def reasons_by_institute(df: pd.DataFrame) -> pd.DataFrame:
    """Factor frequency per institute (as a percentage of that institute's rows)."""
    res = df[df["is_resignation"]].copy()
    exploded = _explode_factors(res)
    # percentage of resignations per institute that mention each factor
    pct = (
        exploded.groupby(["institute", "factor"])
        .size()
        .groupby(level=0)
        .apply(lambda s: (s / s.sum() * 100).round(1))
    )
    return pct.rename("pct").reset_index()


# --------------------------------------------------------------------------- #
# DETE vs TAFE comparison
# --------------------------------------------------------------------------- #
def compare_institutes(df: pd.DataFrame) -> pd.DataFrame:
    """Side-by-side summary statistics for DETE and TAFE resignations."""
    res = df[df["is_resignation"]].copy()

    def _summ(g: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {
                "n_resignations": len(g),
                "dissatisfaction_rate": round(g["dissatisfied"].mean() * 100, 1),
                "mean_age": round(pd.to_numeric(g["age"], errors="coerce").mean(), 1),
                "mean_tenure": round(pd.to_numeric(g["length_of_service"], errors="coerce").mean(), 1),
                "pct_permanent": round((g["employment_status"] == "Permanent").mean() * 100, 1),
            }
        )

    return res.groupby("institute").apply(_summ, include_groups=False).reset_index()


# --------------------------------------------------------------------------- #
# Dissatisfaction breakdowns
# --------------------------------------------------------------------------- #
def dissatisfaction_by(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Dissatisfaction rate (%) and count grouped by ``group_col``."""
    res = df[df["is_resignation"]].copy()
    grp = res.groupby(group_col, observed=True)["dissatisfied"].agg(
        n="count", dissatisfied="sum"
    )
    grp["dissatisfaction_rate_pct"] = (grp["dissatisfied"] / grp["n"] * 100).round(1)
    return grp.reset_index()


def dissatisfaction_by_age(df: pd.DataFrame) -> pd.DataFrame:
    return dissatisfaction_by(df, "age_group")


def dissatisfaction_by_tenure(df: pd.DataFrame) -> pd.DataFrame:
    return dissatisfaction_by(df, "tenure_group")


def dissatisfaction_by_institute(df: pd.DataFrame) -> pd.DataFrame:
    return dissatisfaction_by(df, "institute")


# --------------------------------------------------------------------------- #
# Significant patterns (chi-square)
# --------------------------------------------------------------------------- #
def _chi2(df: pd.DataFrame, var: str) -> dict:
    """Chi-square test of independence between ``var`` and dissatisfaction."""
    from scipy.stats import chi2_contingency

    sub = df[df["is_resignation"]].copy()
    sub[var] = sub[var].astype("category")
    sub["dissatisfied"] = sub["dissatisfied"].astype(int)
    table = pd.crosstab(sub[var], sub["dissatisfied"])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"variable": var, "chi2": np.nan, "p_value": np.nan, "dof": 0, "significant": False}
    chi2, p, dof, _ = chi2_contingency(table)
    return {
        "variable": var,
        "chi2": round(float(chi2), 3),
        "p_value": round(float(p), 4),
        "dof": int(dof),
        "significant": bool(p < 0.05),
    }


def significant_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Run chi-square tests of dissatisfaction against key dimensions."""
    candidates = ["institute", "age_group", "tenure_group", "employment_status"]
    rows = [_chi2(df, c) for c in candidates if c in df.columns]
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Convenience aggregate
# --------------------------------------------------------------------------- #
def summarize(df: pd.DataFrame) -> dict:
    """Headline numbers used by the report and notebook."""
    res = df[df["is_resignation"]]
    return {
        "total_records": len(df),
        "total_resignations": int(res.shape[0]),
        "resignation_rate_pct": round(res.shape[0] / max(len(df), 1) * 100, 1),
        "overall_dissatisfaction_rate_pct": round(res["dissatisfied"].mean() * 100, 1),
        "dete_dissatisfaction_rate_pct": round(
            res[res["institute"] == cfg.DETE_LABEL]["dissatisfied"].mean() * 100, 1
        ),
        "tafe_dissatisfaction_rate_pct": round(
            res[res["institute"] == cfg.TAFE_LABEL]["dissatisfied"].mean() * 100, 1
        ),
        "mean_age": round(pd.to_numeric(res["age"], errors="coerce").mean(), 1),
        "mean_tenure": round(pd.to_numeric(res["length_of_service"], errors="coerce").mean(), 1),
    }


if __name__ == "__main__":
    from src.clean import clean_dete, clean_tafe
    from src.combine import combine_datasets
    from src.load import load_dete, load_tafe
    from src.transform import transform_dete, transform_tafe

    dete = transform_dete(clean_dete(load_dete())[0])
    tafe = transform_tafe(clean_tafe(load_tafe())[0])
    combined = combine_datasets(dete, tafe)

    print("SUMMARY:", summarize(combined))
    print("\nTOP REASONS:\n", top_resignation_reasons(combined))
    print("\nCOMPARE:\n", compare_institutes(combined))
    print("\nBY AGE:\n", dissatisfaction_by_age(combined))
    print("\nBY TENURE:\n", dissatisfaction_by_tenure(combined))
    print("\nSIGNIFICANCE:\n", significant_patterns(combined))
