"""Tests for the combine stage."""

from __future__ import annotations

import pandas as pd

import src.config as cfg
from src.combine import combine_datasets, filter_resignations


def test_combine_adds_institute_labels(dete_transformed, tafe_transformed):
    out = combine_datasets(dete_transformed, tafe_transformed)
    assert set(out["institute"].unique()) == {cfg.DETE_LABEL, cfg.TAFE_LABEL}


def test_combine_marks_resignations(dete_transformed, tafe_transformed):
    out = combine_datasets(dete_transformed, tafe_transformed)
    # the is_resignation flag should be a boolean derived from separation_type
    assert out["is_resignation"].dtype == bool
    assert out["is_resignation"].any()


def test_filter_resignations_keeps_only_resignations(dete_transformed, tafe_transformed):
    out = combine_datasets(dete_transformed, tafe_transformed)
    res = filter_resignations(out)
    assert (res["is_resignation"]).all()
    assert len(res) <= len(out)


def test_combine_preserves_required_columns(combined):
    for col in cfg.COMBINED_REQUIRED_COLUMNS:
        assert col in combined.columns
