"""Tests for the validation stage."""

from __future__ import annotations

import pandas as pd
import pytest

from src.validate import ValidationError, validate


def _base_df():
    return pd.DataFrame(
        {
            "id": [1, 2],
            "institute": ["DETE", "TAFE"],
            "separation_type": ["Resignation", "Resignation"],
            "is_resignation": [True, True],
            "cease_year": [2013, 2014],
            "age": [33.0, 45.0],
            "age_group": ["31-40", "41-50"],
            "length_of_service": [5.0, 3.0],
            "tenure_group": ["4-6", "1-3"],
            "employment_status": ["Permanent", "Casual"],
            "dissatisfied": [True, False],
            "contributing_factors": ["None", "Career Move"],
        }
    )


def test_validate_passes_on_good_data():
    rep = validate(_base_df())
    assert rep.passed is True


def test_validate_fails_on_missing_column():
    df = _base_df().drop(columns=["age"])
    with pytest.raises(ValidationError):
        validate(df)


def test_validate_fails_on_duplicate_rows():
    df = pd.concat([_base_df(), _base_df().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValidationError):
        validate(df)


def test_validate_fails_on_out_of_range_age():
    df = _base_df()
    df.loc[0, "age"] = 200
    with pytest.raises(ValidationError):
        validate(df)


def test_validate_fails_on_bad_institute_value():
    df = _base_df()
    df.loc[0, "institute"] = "UNKNOWN"
    with pytest.raises(ValidationError):
        validate(df)
