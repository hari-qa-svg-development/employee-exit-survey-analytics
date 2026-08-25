"""Clean the raw DETE and TAFE surveys.

Stages performed here:
  * standardize column names (snake_case, stripped)
  * drop columns irrelevant to the exit-analysis question
  * normalize missing-value markers ("Not Stated", blanks, stray whitespace)
  * normalize the survey-specific "Contributing Factors" encodings that the
    dissatisfaction business rule depends on
  * identify and drop exact duplicate records
"""

from __future__ import annotations

import re

import pandas as pd

import src.config as cfg

# Columns we keep for analysis. Anything not listed is treated as irrelevant
# noise (position, classification, region, business unit, the many ratings, etc.)
_DETE_KEEP = [
    "ID",
    "SeparationType",
    "Cease Date",
    "DETE Start Date",
    "Employment Status",
    "Age",
    "Contributing Factors - Career",
    "Contributing Factors - Family",
    "Contributing Factors - Maternity",
    "Contributing Factors - None",
]

_TAFE_KEEP = [
    "Record ID",
    "Institute",
    "CESSATION YEAR",
    "Reason for ceasing employment",
    "Contributing Factors to Ceasing",
    "Gender",
    "Age",
    "Employment Type",
    "Current Length of Service",
] + [c for c, _ in cfg.TAFE_INDIVIDUAL_FACTORS]


def _std(name: str) -> str:
    """Standardize a single raw column name to snake_case."""
    name = str(name).strip().lower()
    name = name.replace("(", " ").replace(")", " ").replace("/", " ")
    name = name.replace(".", " ").replace("-", " ").replace("  ", " ")
    return re.sub(r"\s+", "_", name).strip("_")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip and snake_case every column header."""
    df = df.copy()
    df.columns = [_std(c) for c in df.columns]
    return df


_MISSING_TOKENS = {"", " ", "nan", "na", "none", "not stated", "notstated", "unknown"}


def _normalize_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Turn common null-ish tokens into real NaN and strip string whitespace."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        df[col] = df[col].apply(
            lambda v: float("nan") if (isinstance(v, str) and v.strip().lower() in _MISSING_TOKENS) else v
        )
    return df


def drop_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop exact duplicate rows; return (cleaned_df, n_dropped)."""
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    return df, n_before - len(df)


def _keep_subset(df: pd.DataFrame, raw_keep) -> pd.DataFrame:
    wanted = {_std(c) for c in raw_keep}
    keep = [c for c in df.columns if c in wanted]
    return df[keep].copy()


def clean_dete(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the DETE survey. Returns (cleaned_df, cleaning_report)."""
    report: dict = {}
    df = standardize_columns(df)
    report["columns_after_standardize"] = list(df.columns)

    before_cols = set(df.columns)
    df = _keep_subset(df, _DETE_KEEP)
    report["dropped_columns"] = sorted(before_cols - set(df.columns))

    df = _normalize_missing(df)

    # Normalize the four contributing-factor columns: a null/blank means the
    # factor was NOT selected, which the dissatisfaction rule encodes as "-".
    for col in [
        "contributing_factors_career",
        "contributing_factors_family",
        "contributing_factors_maternity",
        "contributing_factors_none",
    ]:
        if col in df.columns:
            df[col] = df[col].fillna(cfg.DETE_NOT_SELECTED_TOKEN).astype(str).str.strip()

    df, n_dup = drop_duplicates(df)
    report["duplicates_dropped"] = n_dup
    report["rows_after"] = len(df)
    return df, report


def clean_tafe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the TAFE survey. Returns (cleaned_df, cleaning_report)."""
    report: dict = {}
    df = standardize_columns(df)
    report["columns_after_standardize"] = list(df.columns)

    before_cols = set(df.columns)
    df = _keep_subset(df, _TAFE_KEEP)
    report["dropped_columns"] = sorted(before_cols - set(df.columns))

    df = _normalize_missing(df)

    # Normalize the individual contributing-factor flags to booleans.
    for col, _ in cfg.TAFE_INDIVIDUAL_FACTORS:
        std = _std(col)
        if std in df.columns:
            df[std] = df[std].map(
                lambda v: True if str(v).strip().lower() in ("yes", "true", "1") else (False if pd.notna(v) else pd.NA)
            )

    df, n_dup = drop_duplicates(df)
    report["duplicates_dropped"] = n_dup
    report["rows_after"] = len(df)
    return df, report


if __name__ == "__main__":
    from src.load import load_dete, load_tafe

    d, dr = clean_dete(load_dete())
    t, tr = clean_tafe(load_tafe())
    print("DETE cleaned:", d.shape, dr)
    print("TAFE cleaned:", t.shape, tr)
