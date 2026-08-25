"""Project-wide configuration and shared constants.

All magic strings, column names, business-rule thresholds and file paths used by
the pipeline live here so the stages stay consistent and easy to audit.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

DETE_RAW_PATH = DATA_RAW / "dete_exit_survey.csv"
TAFE_RAW_PATH = DATA_RAW / "tafe_survey.csv"
COMBINED_PATH = DATA_PROCESSED / "combined_exit_survey.csv"

# --------------------------------------------------------------------------- #
# Institute labels
# --------------------------------------------------------------------------- #
DETE_LABEL = "DETE"
TAFE_LABEL = "TAFE"

# --------------------------------------------------------------------------- #
# Separation-type handling
# --------------------------------------------------------------------------- #
# Values (case-insensitive) in the separation/reason column that mean the
# employee quit of their own accord and are kept for the resignation analysis.
RESIGNATION_KEYWORDS = ("resignation",)

# Non-resignation separation types we expect to see and deliberately filter out.
NON_RESIGNATION_TYPES = {
    "Retrenchment",
    "Retirement",
    "Transfer",
    "Termination",
    "Invalidity",
    "Contract Expired",
    "Other",
}

# --------------------------------------------------------------------------- #
# Dissatisfaction business rule
# --------------------------------------------------------------------------- #
# DETE: the four "Contributing Factors - *" columns hold the factor name when
# selected and "-" when not selected. An employee who selected NONE of the
# benign/structural factors (Career, Family, Maternity, None) is treated as
# having left due to dissatisfaction with the role/organisation. This mirrors
# the well-documented methodology for these surveys.
DETE_CONTRIBUTING_FACTORS = [
    "Contributing Factors - Career",
    "Contributing Factors - Family",
    "Contributing Factors - Maternity",
    "Contributing Factors - None",
]
DETE_NOT_SELECTED_TOKEN = "-"

# TAFE: the free-text "Contributing Factors to Ceasing" field lists selected
# factors separated by ";". We flag dissatisfaction when that list contains the
# literal token below.
TAFE_DISSATISFACTION_TOKEN = "Dissatisfaction"

# --------------------------------------------------------------------------- #
# Age groups (upper bound inclusive). Anything above the last bound -> ">60".
# --------------------------------------------------------------------------- #
AGE_BINS = [0, 30, 40, 50, 60, 200]
AGE_LABELS = ["<=30", "31-40", "41-50", "51-60", ">60"]

# Midpoints used when we only have an age *range* in the raw data.
AGE_RANGE_MIDPOINTS = {
    "20 or younger": 20,
    "21-25": 23,
    "26-30": 28,
    "31-35": 33,
    "36-40": 38,
    "41-45": 43,
    "46-50": 48,
    "51-55": 53,
    "56 or older": 58,
}

# --------------------------------------------------------------------------- #
# Tenure (length of service) groups.
# --------------------------------------------------------------------------- #
TENURE_BINS = [-0.01, 1, 3, 6, 10, 1000]
TENURE_LABELS = ["Less than 1", "1-3", "4-6", "7-10", "More than 10"]

# Midpoints for TAFE's categorical "Current Length of Service" field.
LENGTH_OF_SERVICE_MIDPOINTS = {
    "Less than 1": 0.5,
    "1-2": 1.5,
    "3-4": 3.5,
    "5-6": 5.5,
    "7-8": 7.5,
    "9-10": 9.5,
    "11-12": 11.5,
    "13-14": 13.5,
    "15-16": 15.5,
    "17-18": 17.5,
    "19-20": 19.5,
    "More than 20": 22.0,
}

# --------------------------------------------------------------------------- #
# Validation guards
# --------------------------------------------------------------------------- #
VALID_CESSATION_YEARS = range(2009, 2019)  # plausible survey window
MIN_AGE = 18
MAX_AGE = 80
MIN_TENURE = 0
MAX_TENURE = 50

# TAFE: the individual contributing-factor columns and their human-readable
# factor label (used both to build the combined free-text field and to derive
# the dissatisfaction flag).
TAFE_INDIVIDUAL_FACTORS = [
    ("Contributing Factors. Career Move - Public Sector Employees", "Career Move - Public Sector Employees"),
    ("Contributing Factors. Career Move - Private Sector Employees", "Career Move - Private Sector Employees"),
    ("Contributing Factors. Career Move - Self-employment", "Career Move - Self-employment"),
    ("Contributing Factors. Ill Health", "Ill Health"),
    ("Contributing Factors. Maternity/Family", "Maternity/Family"),
    ("Contributing Factors. Dissatisfaction", "Dissatisfaction"),
    ("Contributing Factors. External Regulation", "External Regulation"),
    ("Contributing Factors. Other", "Other"),
    ("Contributing Factors. None", "None"),
]
COMBINED_REQUIRED_COLUMNS = [
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
]

# --------------------------------------------------------------------------- #
# Defaults / misc
# --------------------------------------------------------------------------- #
RANDOM_SEED = 42
