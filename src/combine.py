"""Combine the transformed DETE and TAFE frames into one standardized dataset."""

from __future__ import annotations

import pandas as pd

import src.config as cfg


def _finalize(df: pd.DataFrame, institute: str) -> pd.DataFrame:
    df = df.copy()
    df["institute"] = institute
    df["is_resignation"] = (
        df["separation_type"].astype(str).str.lower().str.contains("resignation", na=False)
    )
    return df


def combine_datasets(dete: pd.DataFrame, tafe: pd.DataFrame) -> pd.DataFrame:
    """Concatenate both surveys into a single standardized schema.

    Only the shared analysis columns are kept; source-specific columns are
    dropped so the resulting frame is uniform across institutes.
    """
    dete = _finalize(dete, cfg.DETE_LABEL)
    tafe = _finalize(tafe, cfg.TAFE_LABEL)

    cols = [
        "id",
        "institute",
        "separation_type",
        "is_resignation",
        "cease_year",
        "age",
        "age_group",
        "length_of_service",
        "tenure_group",
        "employment_status",
        "dissatisfied",
        "contributing_factors",
    ]
    dete = dete[cols].copy()
    tafe = tafe[cols].copy()
    combined = pd.concat([dete, tafe], ignore_index=True)
    return combined


def filter_resignations(df: pd.DataFrame) -> pd.DataFrame:
    """Return only the rows that are genuine resignations."""
    return df[df["is_resignation"]].copy().reset_index(drop=True)


if __name__ == "__main__":
    from src.clean import clean_dete, clean_tafe
    from src.load import load_dete, load_tafe
    from src.transform import transform_dete, transform_tafe

    dete = transform_dete(clean_dete(load_dete())[0])
    tafe = transform_tafe(clean_tafe(load_tafe())[0])
    combined = combine_datasets(dete, tafe)
    print("Combined:", combined.shape)
    print(combined["institute"].value_counts())
    print("Resignations:", combined["is_resignation"].sum())
