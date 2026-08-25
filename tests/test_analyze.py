"""Tests for the analysis stage."""

from __future__ import annotations

import pandas as pd

from src.analyze import (
    compare_institutes,
    dissatisfaction_by_age,
    significant_patterns,
    summarize,
    top_resignation_reasons,
)


def test_top_resignation_reasons_returns_counts(combined):
    out = top_resignation_reasons(combined)
    assert "factor" in out.columns and "count" in out.columns
    assert out["count"].sum() > 0


def test_compare_institutes_has_both(combined):
    out = compare_institutes(combined)
    assert set(out["institute"]) == {"DETE", "TAFE"}


def test_dissatisfaction_by_age_groups_present(combined):
    out = dissatisfaction_by_age(combined)
    assert "dissatisfaction_rate_pct" in out.columns
    assert (out["dissatisfaction_rate_pct"] >= 0).all()


def test_significant_patterns_includes_institute(combined):
    out = significant_patterns(combined)
    assert "institute" in out["variable"].values
    assert "p_value" in out.columns


def test_summarize_returns_expected_keys(combined):
    out = summarize(combined)
    for key in ["total_records", "total_resignations", "overall_dissatisfaction_rate_pct"]:
        assert key in out
