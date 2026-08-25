"""Generate reproducible, intentionally-messy raw exit-survey datasets.

The real DETE and TAFE employee exit surveys are not reliably redistributable,
so this script fabricates datasets that reproduce their *structure and the kinds
of messiness* analysts actually face:

  * inconsistent / spaced column headers
  * mixed date formats and missing dates
  * categorical ranges for age and length of service
  * benign "Not Stated" / blank / NaN missing markers
  * duplicate records
  * the survey-specific "Contributing Factors" encodings that drive the
    dissatisfaction business rule

Running the script overwrites ``data/raw/dete_exit_survey.csv`` and
``data/raw/tafe_survey.csv``. It is deterministic (fixed seed) so the whole
project is reproducible.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import src.config as cfg

rng = np.random.default_rng(cfg.RANDOM_SEED)


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _choice(options, probabilities=None, size=None):
    return rng.choice(options, size=size, p=probabilities)


def _missing_mask(size, rate):
    """Return a boolean mask marking values that should be missing."""
    return rng.random(size) < rate


# --------------------------------------------------------------------------- #
# DETE
# --------------------------------------------------------------------------- #
DETE_COLUMNS = [
    "ID",
    "SeparationType",
    "Cease Date",
    "DETE Start Date",
    "Role Start Date",
    "Position",
    "Classification",
    "Region",
    "Business Unit",
    "Employment Status",
    "Career Move - Intent",
    "Career Move - Desire",
    "Contributing Factors - Career",
    "Contributing Factors - Family",
    "Contributing Factors - Maternity",
    "Contributing Factors - None",
    "Professional Development",
    "Opportunities for Promotion",
    "Work/Life Balance",
    "Stress and pressure support",
    "Performance of supervisor",
    "Peer support",
    "Initiative",
    "Skills development",
    "Coaching",
    "Rating - Career Move Desire",
    "Rating - Career Move Intent",
    "Rating - Overall Experience",
    "Rating - Self-development",
    "Rating - Work Life Balance",
    "Rating - Staff Relations",
    "Age",
]

DETE_SEPARATION = [
    "Resignation",
    "Resignation (Status Quo)",
    "Resignation (Other)",
    "Retrenchment",
    "Retirement",
    "Transfer",
    "Termination",
    "Invalidity",
    "Other",
]
DETE_SEPARATION_P = [0.45, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.12]

EMPLOYMENT_STATUS = ["Permanent", "Temporary", "Casual", "Fixed Term"]
EMPLOYMENT_P = [0.55, 0.20, 0.15, 0.10]

AGE_RANGES = list(cfg.AGE_RANGE_MIDPOINTS.keys())
AGE_P = [0.05, 0.10, 0.15, 0.18, 0.17, 0.15, 0.10, 0.07, 0.03]


def _random_date(start_year, end_year):
    year = rng.integers(start_year, end_year + 1)
    month = rng.integers(1, 13)
    day = rng.integers(1, 28)
    return f"{year:04d}/{month:02d}/{day:02d}"


def _random_month_only(start_year, end_year):
    year = rng.integers(start_year, end_year + 1)
    month = rng.integers(1, 13)
    return f"{year:04d}/{month:02d}"


def make_dete(n: int = 600) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        sep = _choice(DETE_SEPARATION, DETE_SEPARATION_P)
        cease = _random_date(2009, 2018)
        start = _random_date(1990, 2017)
        role_start = _random_date(1990, 2017)

        # Contributing factors: each selected independently; not-selected -> "-"
        cf_career = "Career Move" if rng.random() < 0.25 else "-"
        cf_family = "Maternity/Family" if rng.random() < 0.12 else "-"
        cf_maternity = "Maternity/Family" if rng.random() < 0.10 else "-"
        cf_none = "None" if rng.random() < 0.18 else "-"

        row = {
            "ID": i,
            "SeparationType": sep,
            "Cease Date": cease,
            "DETE Start Date": start,
            "Role Start Date": role_start,
            "Position": _choice(["Teacher", "Administrator", "Manager", "Consultant", "Not Stated"]),
            "Classification": _choice(["AO4", "AO5", "AO6", "SO", "Not Stated"]),
            "Region": _choice(["North", "South", "Metro", "Regional", "Not Stated"]),
            "Business Unit": _choice(["Schools", "VET", "Corporate", "Not Stated"]),
            "Employment Status": _choice(EMPLOYMENT_STATUS, EMPLOYMENT_P),
            "Career Move - Intent": _choice(["Yes", "No"]),
            "Career Move - Desire": _choice(["Yes", "No"]),
            "Contributing Factors - Career": cf_career,
            "Contributing Factors - Family": cf_family,
            "Contributing Factors - Maternity": cf_maternity,
            "Contributing Factors - None": cf_none,
            "Professional Development": _choice(["Agree", "Neutral", "Disagree"]),
            "Opportunities for Promotion": _choice(["Agree", "Neutral", "Disagree"]),
            "Work/Life Balance": _choice(["Agree", "Neutral", "Disagree"]),
            "Stress and pressure support": _choice(["Agree", "Neutral", "Disagree"]),
            "Performance of supervisor": _choice(["Agree", "Neutral", "Disagree"]),
            "Peer support": _choice(["Agree", "Neutral", "Disagree"]),
            "Initiative": _choice(["Agree", "Neutral", "Disagree"]),
            "Skills development": _choice(["Agree", "Neutral", "Disagree"]),
            "Coaching": _choice(["Agree", "Neutral", "Disagree"]),
            "Rating - Career Move Desire": rng.integers(1, 6),
            "Rating - Career Move Intent": rng.integers(1, 6),
            "Rating - Overall Experience": rng.integers(1, 6),
            "Rating - Self-development": rng.integers(1, 6),
            "Rating - Work Life Balance": rng.integers(1, 6),
            "Rating - Staff Relations": rng.integers(1, 6),
            "Age": _choice(AGE_RANGES, AGE_P),
        }
        rows.append(row)

    df = pd.DataFrame(rows, columns=DETE_COLUMNS)

    # ---- inject messiness ------------------------------------------------ #
    # 1. Some dates are month-only (no day) and some are missing entirely.
    month_only = _missing_mask(len(df), 0.15)
    df.loc[month_only, "Cease Date"] = df.loc[month_only, "Cease Date"].apply(
        lambda d: d[:7] if isinstance(d, str) else d
    )
    df.loc[month_only, "DETE Start Date"] = df.loc[month_only, "DETE Start Date"].apply(
        lambda d: d[:7] if isinstance(d, str) else d
    )

    miss_dates = _missing_mask(len(df), 0.05)
    df.loc[miss_dates, ["Cease Date", "DETE Start Date"]] = np.nan

    # 2. Some age values are missing / "Not Stated".
    age_missing = _missing_mask(len(df), 0.10)
    df.loc[age_missing, "Age"] = "Not Stated"

    # 3. Inject duplicate records (full-row copies).
    dup_idx = rng.choice(df.index, size=15, replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

    # 4. Random stray whitespace in a couple of column headers.
    df = df.rename(columns={"SeparationType": "SeparationType "})
    return df


# --------------------------------------------------------------------------- #
# TAFE
# --------------------------------------------------------------------------- #
TAFE_COLUMNS = (
    ["Record ID", "Institute", "WorkArea", "CESSATION YEAR", "Reason for ceasing employment"]
    + [c for c, _ in cfg.TAFE_INDIVIDUAL_FACTORS]
    + ["Contributing Factors to Ceasing", "Gender", "Age", "Employment Type", "Current Length of Service"]
)

TAFE_REASON = [
    "Resignation",
    "Contract Expired",
    "Retirement",
    "Transfer",
    "Other",
    "Termination of Employment",
]
TAFE_REASON_P = [0.50, 0.12, 0.08, 0.05, 0.15, 0.10]

TAFE_INSTITUTES = ["Southbank", "Brisbane", "Gold Coast", "Sunshine Coast", "Not Stated"]
LOS_CATEGORIES = list(cfg.LENGTH_OF_SERVICE_MIDPOINTS.keys())
LOS_P = [0.10, 0.18, 0.18, 0.15, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]


def make_tafe(n: int = 500) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        reason = _choice(TAFE_REASON, TAFE_REASON_P)
        year = int(rng.integers(2010, 2019))

        # Individual contributing factors (booleans), then build combined field.
        selected = []
        indiv = {}
        for col, label in cfg.TAFE_INDIVIDUAL_FACTORS:
            picked = rng.random() < 0.20
            indiv[col] = "Yes" if picked else "No"
            if picked:
                selected.append(label)
        combined = "; ".join(selected) if selected else "None"

        row = {
            "Record ID": i,
            "Institute": _choice(TAFE_INSTITUTES),
            "WorkArea": _choice(["Delivery", "Corporate", "Library", "Student Services", "Not Stated"]),
            "CESSATION YEAR": year,
            "Reason for ceasing employment": reason,
            "Contributing Factors to Ceasing": combined,
            "Gender": _choice(["Male", "Female", "Not Stated"]),
            "Age": _choice(AGE_RANGES, AGE_P),
            "Employment Type": _choice(EMPLOYMENT_STATUS, EMPLOYMENT_P),
            "Current Length of Service": _choice(LOS_CATEGORIES, LOS_P),
        }
        row.update(indiv)
        rows.append(row)

    df = pd.DataFrame(rows, columns=TAFE_COLUMNS)

    # ---- inject messiness ------------------------------------------------ #
    # 1. Messy header casing / spacing to exercise standardization.
    df = df.rename(
        columns={
            "CESSATION YEAR": " CESSATION YEAR ",
            "Reason for ceasing employment": "Reason for ceasing employment",
        }
    )

    # 2. Some cessation years and ages are missing.
    yr_missing = _missing_mask(len(df), 0.06)
    df.loc[yr_missing, " CESSATION YEAR "] = np.nan
    age_missing = _missing_mask(len(df), 0.08)
    df.loc[age_missing, "Age"] = "Not Stated"

    # 3. Some length-of-service values blank.
    los_missing = _missing_mask(len(df), 0.07)
    df.loc[los_missing, "Current Length of Service"] = ""

    # 4. Duplicate a few records.
    dup_idx = rng.choice(df.index, size=12, replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)
    return df


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    cfg.DATA_RAW.mkdir(parents=True, exist_ok=True)
    dete = make_dete()
    tafe = make_tafe()
    dete.to_csv(cfg.DETE_RAW_PATH, index=False)
    tafe.to_csv(cfg.TAFE_RAW_PATH, index=False)
    print(f"Wrote {len(dete):,} DETE rows -> {cfg.DETE_RAW_PATH}")
    print(f"Wrote {len(tafe):,} TAFE rows -> {cfg.TAFE_RAW_PATH}")


if __name__ == "__main__":
    main()
