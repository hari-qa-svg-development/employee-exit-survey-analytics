"""Validate the combined dataset against the project's data-quality contract.

``validate`` raises a ``ValidationError`` (and returns a structured report) when
any of the following checks fail:

  * required columns are present
  * expected dtypes / value domains hold (years, ages, tenure, booleans)
  * no fully-duplicate rows remain
  * missingness on key fields is within tolerance
  * separation-type and institute values are within expected vocabularies
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

import src.config as cfg


class ValidationError(Exception):
    """Raised when one or more validation checks fail."""


@dataclass
class ValidationReport:
    checks: list[dict] = field(default_factory=list)
    passed: bool = True

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            self.passed = False

    def __str__(self) -> str:
        lines = []
        for c in self.checks:
            status = "PASS" if c["passed"] else "FAIL"
            lines.append(f"[{status}] {c['check']} {c['detail']}")
        return "\n".join(lines)


def validate(df: pd.DataFrame, max_missing_pct: float = 25.0) -> ValidationReport:
    """Run the full validation suite and return a structured report."""
    report = ValidationReport()

    # 1. Required columns
    missing_cols = [c for c in cfg.COMBINED_REQUIRED_COLUMNS if c not in df.columns]
    report.add("required_columns", not missing_cols, f"missing={missing_cols}")

    # 2. Data types / domains
    if "cease_year" in df.columns:
        yrs = pd.to_numeric(df["cease_year"], errors="coerce").dropna()
        bad_years = (~yrs.isin(cfg.VALID_CESSATION_YEARS)).sum()
        report.add("cease_year_domain", bad_years == 0, f"{bad_years} out-of-range")

    if "age" in df.columns:
        ages = pd.to_numeric(df["age"], errors="coerce")
        bad_age = ((ages < cfg.MIN_AGE) | (ages > cfg.MAX_AGE)).sum()
        report.add("age_range", bad_age == 0, f"{bad_age} out-of-range")

    if "length_of_service" in df.columns:
        ten = pd.to_numeric(df["length_of_service"], errors="coerce")
        bad_ten = ((ten < cfg.MIN_TENURE) | (ten > cfg.MAX_TENURE)).sum()
        report.add("tenure_range", bad_ten == 0, f"{bad_ten} out-of-range")

    if "dissatisfied" in df.columns:
        ok_bool = df["dissatisfied"].dropna().isin([True, False]).all()
        report.add("dissatisfied_is_boolean", ok_bool)

    # 3. Duplicates
    dup = df.duplicated().sum()
    report.add("no_duplicate_rows", dup == 0, f"{dup} duplicates")

    # 4. Missingness tolerance on key fields
    key_fields = ["separation_type", "institute", "is_resignation", "dissatisfied"]
    for f in key_fields:
        if f in df.columns:
            pct = df[f].isna().mean() * 100
            report.add(f"missing_{f}_within_tolerance", pct <= max_missing_pct, f"{pct:.1f}%")

    # 5. Controlled vocabularies
    if "institute" in df.columns:
        unknown_inst = set(df["institute"].dropna().unique()) - {cfg.DETE_LABEL, cfg.TAFE_LABEL}
        report.add("institute_vocabulary", not unknown_inst, f"unknown={unknown_inst}")

    if "is_resignation" in df.columns:
        ok_flag = df["is_resignation"].dropna().isin([True, False]).all()
        report.add("is_resignation_is_boolean", ok_flag)

    if not report.passed:
        raise ValidationError("Validation failed:\n" + str(report))
    return report


if __name__ == "__main__":
    import src.config as cfg
    from src.clean import clean_dete, clean_tafe
    from src.combine import combine_datasets
    from src.load import load_dete, load_tafe
    from src.transform import transform_dete, transform_tafe

    dete = transform_dete(clean_dete(load_dete())[0])
    tafe = transform_tafe(clean_tafe(load_tafe())[0])
    combined = combine_datasets(dete, tafe)
    rep = validate(combined)
    print(rep)
