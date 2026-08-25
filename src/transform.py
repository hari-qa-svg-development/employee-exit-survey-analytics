"""Transform the cleaned DETE/TAFE frames into analysis-ready columns.

Responsibilities:
  * parse the various date encodings into a numeric cessation year
  * compute employee tenure (DETE from start/cease dates; TAFE from the
    categorical length-of-service field)
  * convert the age *ranges* into numeric midpoints and age groups
  * bucket tenure into groups
  * apply the dissatisfaction business rule for each survey
  * build a tidy "contributing_factors" list per employee
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import src.config as cfg


# --------------------------------------------------------------------------- #
# Dates / years
# --------------------------------------------------------------------------- #
def extract_year(series: pd.Series) -> pd.Series:
    """Pull the 4-digit year out of messy date strings (YYYY/MM/DD or YYYY/MM)."""
    return series.astype(str).str.extract(r"(\d{4})")[0].astype("float")


def dete_tenure(cease_year: pd.Series, start_year: pd.Series) -> pd.Series:
    """Tenure in years = cease year - DETE start year (negative -> NaN)."""
    tenure = cease_year - start_year
    tenure = tenure.where(tenure >= 0)
    return tenure


# --------------------------------------------------------------------------- #
# Age
# --------------------------------------------------------------------------- #
def map_age_ranges(series: pd.Series) -> pd.Series:
    """Map an age *range* string to its numeric midpoint (missing -> NaN)."""
    return series.map(cfg.AGE_RANGE_MIDPOINTS)


def add_age_group(df: pd.DataFrame, age_col: str = "age") -> pd.DataFrame:
    df = df.copy()
    df["age_group"] = pd.cut(
        df[age_col], bins=cfg.AGE_BINS, labels=cfg.AGE_LABELS, right=True
    ).astype(object)
    return df


# --------------------------------------------------------------------------- #
# Tenure / length of service
# --------------------------------------------------------------------------- #
def map_length_of_service(series: pd.Series) -> pd.Series:
    """Map TAFE's categorical length-of-service to a numeric midpoint."""
    return series.map(cfg.LENGTH_OF_SERVICE_MIDPOINTS)


def add_tenure_group(df: pd.DataFrame, tenure_col: str = "length_of_service") -> pd.DataFrame:
    df = df.copy()
    df["tenure_group"] = pd.cut(
        df[tenure_col], bins=cfg.TENURE_BINS, labels=cfg.TENURE_LABELS, right=True
    ).astype(object)
    return df


# --------------------------------------------------------------------------- #
# Dissatisfaction (business rule)
# --------------------------------------------------------------------------- #
def flag_dissatisfied_dete(df: pd.DataFrame) -> pd.Series:
    """DETE rule: dissatisfied when NONE of the four benign factors was selected.

    Each contributing-factor column holds the factor name when selected and "-"
    when not. An employee who selected none of Career/Family/Maternity/None is
    treated as having left due to dissatisfaction.
    """
    cols = [
        "contributing_factors_career",
        "contributing_factors_family",
        "contributing_factors_maternity",
        "contributing_factors_none",
    ]
    cols = [c for c in cols if c in df.columns]
    selected = df[cols].apply(lambda c: ~c.isin([cfg.DETE_NOT_SELECTED_TOKEN]))
    return (selected.sum(axis=1) == 0)


def flag_dissatisfied_tafe(df: pd.DataFrame) -> pd.Series:
    """TAFE rule: dissatisfied when the combined field lists 'Dissatisfaction'."""
    field = df.get("contributing_factors_to_ceasing")
    if field is None:
        return pd.Series(False, index=df.index)
    return (
        field.astype(str)
        .str.lower()
        .str.contains(cfg.TAFE_DISSATISFACTION_TOKEN.lower(), na=False)
    )


def build_contributing_factors_dete(df: pd.DataFrame) -> pd.Series:
    """Reconstruct the selected factors as a '; '-joined string for DETE."""
    mapping = {
        "contributing_factors_career": "Career Move",
        "contributing_factors_family": "Maternity/Family",
        "contributing_factors_maternity": "Maternity/Family",
        "contributing_factors_none": "None",
    }
    mapping = {k: v for k, v in mapping.items() if k in df.columns}
    out = []
    for _, row in df.iterrows():
        selected = [
            label
            for col, label in mapping.items()
            if row[col] != cfg.DETE_NOT_SELECTED_TOKEN
        ]
        out.append("; ".join(selected) if selected else "None")
    return pd.Series(out, index=df.index)


# --------------------------------------------------------------------------- #
# Full transforms
# --------------------------------------------------------------------------- #
def transform_dete(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DETE frame with the unified analysis columns populated."""
    df = df.copy()
    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df = df.rename(
        columns={
            "separationtype": "separation_type",
            "employment_status": "employment_status",
        }
    )

    cease_year = extract_year(df["cease_date"])
    start_year = extract_year(df["dete_start_date"])
    df["cease_year"] = cease_year.astype("Int64")
    df["length_of_service"] = dete_tenure(cease_year, start_year)

    df["age"] = map_age_ranges(df["age"])

    df["dissatisfied"] = flag_dissatisfied_dete(df)
    df["contributing_factors"] = build_contributing_factors_dete(df)

    df = add_age_group(df)
    df = add_tenure_group(df)
    return df


def transform_tafe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a TAFE frame with the unified analysis columns populated."""
    df = df.copy()
    df["id"] = pd.to_numeric(df["record_id"], errors="coerce").astype("Int64")
    df = df.rename(
        columns={
            "reason_for_ceasing_employment": "separation_type",
            "employment_type": "employment_status",
            "cessation_year": "cease_year",
        }
    )

    df["cease_year"] = pd.to_numeric(df["cease_year"], errors="coerce").astype("Int64")
    df["length_of_service"] = map_length_of_service(df["current_length_of_service"])
    df["age"] = map_age_ranges(df["age"])

    df["dissatisfied"] = flag_dissatisfied_tafe(df)

    field = df.get("contributing_factors_to_ceasing")
    df["contributing_factors"] = field.fillna("None") if field is not None else "None"

    df = add_age_group(df)
    df = add_tenure_group(df)
    return df


if __name__ == "__main__":
    from src.clean import clean_dete, clean_tafe
    from src.load import load_dete, load_tafe

    d = transform_dete(clean_dete(load_dete())[0])
    t = transform_tafe(clean_tafe(load_tafe())[0])
    cols = ["id", "separation_type", "cease_year", "age", "age_group", "length_of_service", "tenure_group", "dissatisfied", "contributing_factors"]
    print("DETE:\n", d[cols].head())
    print("TAFE:\n", t[cols].head())
