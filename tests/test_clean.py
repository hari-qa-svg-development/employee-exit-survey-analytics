"""Tests for the cleaning stage."""

from __future__ import annotations

import pandas as pd

from src.clean import clean_dete, clean_tafe, drop_duplicates, standardize_columns


def test_standardize_columns_lowercases_and_snake_cases():
    df = pd.DataFrame(columns=["  CESSATION YEAR ", "Reason.for.ceasing (employment)"])
    out = standardize_columns(df)
    assert out.columns.tolist() == ["cessation_year", "reason_for_ceasing_employment"]


def test_clean_dete_drops_irrelevant_columns(raw_dete):
    out, _ = clean_dete(raw_dete)
    # position / region / ratings should be gone; core fields should remain
    assert "position" not in out.columns
    assert "region" not in out.columns
    for col in ["id", "separationtype", "cease_date", "age"]:
        assert col in out.columns


def test_clean_dete_normalizes_not_stated_to_nan():
    df = pd.DataFrame(
        {
            "ID": ["1"],
            "SeparationType": ["Resignation"],
            "Cease Date": ["2013/01/01"],
            "DETE Start Date": ["2005/01/01"],
            "Employment Status": ["Permanent"],
            "Age": ["Not Stated"],
            "Contributing Factors - Career": ["-"],
            "Contributing Factors - Family": ["-"],
            "Contributing Factors - Maternity": ["-"],
            "Contributing Factors - None": ["-"],
        }
    )
    out, _ = clean_dete(df)
    assert pd.isna(out["age"].iloc[0])


def test_clean_dete_normalizes_contributing_factor_blanks_to_dash():
    df = pd.DataFrame(
        {
            "ID": ["1", "2"],
            "SeparationType": ["Resignation", "Resignation"],
            "Cease Date": ["2013/01/01", "2013/01/01"],
            "DETE Start Date": ["2005/01/01", "2005/01/01"],
            "Employment Status": ["Permanent", "Permanent"],
            "Age": ["31-35", "31-35"],
            "Contributing Factors - Career": [None, "Career Move"],
            "Contributing Factors - Family": ["-", "-"],
            "Contributing Factors - Maternity": ["-", "-"],
            "Contributing Factors - None": ["-", "-"],
        }
    )
    out, _ = clean_dete(df)
    # None should normalize to "-"; "Career Move" should be preserved
    assert out["contributing_factors_career"].iloc[0] == "-"
    assert out["contributing_factors_career"].iloc[1] == "Career Move"


def test_drop_duplicates_removes_exact_copies():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    out, n = drop_duplicates(df)
    assert n == 1
    assert len(out) == 2


def test_clean_tafe_keeps_expected_columns(raw_tafe):
    out, _ = clean_tafe(raw_tafe)
    assert "record_id" in out.columns
    assert "contributing_factors_to_ceasing" in out.columns
    assert "workarea" not in out.columns
