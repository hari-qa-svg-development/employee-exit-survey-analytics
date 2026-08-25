"""Load raw exit-survey CSVs and profile their structure.

These helpers keep IO in one place and produce a lightweight, human-readable
profile (shape, dtypes, missing-value counts) that the notebook and reports can
reuse.
"""

from __future__ import annotations

import pandas as pd

import src.config as cfg


def load_dete(path=cfg.DETE_RAW_PATH) -> pd.DataFrame:
    """Load the raw DETE exit survey, keeping everything as-is (strings)."""
    return pd.read_csv(path, dtype=str, keep_default_na=True)


def load_tafe(path=cfg.TAFE_RAW_PATH) -> pd.DataFrame:
    """Load the raw TAFE survey, keeping everything as-is (strings)."""
    return pd.read_csv(path, dtype=str, keep_default_na=True)


def profile(df: pd.DataFrame) -> pd.DataFrame:
    """Return a per-column profile: dtype, non-null count, missing count.

    The output is a small tidy DataFrame suitable for printing or logging.
    """
    report = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "non_null": df.notna().sum(),
            "missing": df.isna().sum(),
            "missing_pct": (df.isna().mean() * 100).round(1),
            "n_unique": df.nunique(dropna=True),
        }
    )
    return report


def profile_pair(dete: pd.DataFrame, tafe: pd.DataFrame) -> dict:
    """Profile both datasets and return a combined summary dict."""
    return {
        "dete_shape": dete.shape,
        "tafe_shape": tafe.shape,
        "dete_columns": list(dete.columns),
        "tafe_columns": list(tafe.columns),
        "dete_profile": profile(dete),
        "tafe_profile": profile(tafe),
    }


if __name__ == "__main__":
    dete = load_dete()
    tafe = load_tafe()
    print("DETE shape:", dete.shape)
    print("TAFE shape:", tafe.shape)
    print("\nDETE profile:\n", profile(dete))
    print("\nTAFE profile:\n", profile(tafe))
