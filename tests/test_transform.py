"""Tests for the transformation stage."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.clean import clean_dete, clean_tafe
from src.transform import (
    add_age_group,
    add_tenure_group,
    dete_tenure,
    extract_year,
    flag_dissatisfied_dete,
    flag_dissatisfied_tafe,
    map_age_ranges,
    transform_dete,
    transform_tafe,
)


def test_extract_year_handles_full_and_partial_dates():
    s = pd.Series(["2013/05/22", "2012/11", "not-a-date"])
    out = extract_year(s)
    assert out.iloc[0] == 2013
    assert out.iloc[1] == 2012
    assert pd.isna(out.iloc[2])


def test_dete_tenure_positive_and_negative():
    cease = pd.Series([2013.0, 2010.0])
    start = pd.Series([2005.0, 2015.0])
    out = dete_tenure(cease, start)
    assert out.iloc[0] == 8
    assert pd.isna(out.iloc[1])  # negative tenure -> NaN


def test_map_age_ranges_known_keys():
    out = map_age_ranges(pd.Series(["31-35", "56 or older", "Not Stated"]))
    assert out.iloc[0] == 33
    assert out.iloc[1] == 58
    assert pd.isna(out.iloc[2])


def test_add_age_group_labels():
    df = pd.DataFrame({"age": [20.0, 33.0, 43.0, 53.0, 65.0]})
    out = add_age_group(df)
    assert out["age_group"].tolist() == ["<=30", "31-40", "41-50", "51-60", ">60"]


def test_add_tenure_group_labels():
    df = pd.DataFrame({"length_of_service": [0.5, 2.0, 4.0, 8.0, 15.0]})
    out = add_tenure_group(df)
    assert out["tenure_group"].tolist() == ["Less than 1", "1-3", "4-6", "7-10", "More than 10"]


def test_flag_dissatisfied_dete_all_dash_is_true(tiny_dete):
    df = clean_dete(tiny_dete)[0]
    out = flag_dissatisfied_dete(df)
    # row 0: all four factors "-"; row 1: Career Move selected -> not dissatisfied
    assert bool(out.iloc[0]) is True
    assert bool(out.iloc[1]) is False


def test_flag_dissatisfied_tafe_detects_token():
    df = pd.DataFrame(
        {"contributing_factors_to_ceasing": ["Career Move; Dissatisfaction", "None", np.nan]}
    )
    out = flag_dissatisfied_tafe(df)
    assert out.tolist() == [True, False, False]


def test_transform_dete_produces_unified_columns(tiny_dete):
    df = transform_dete(clean_dete(tiny_dete)[0])
    for col in ["id", "separation_type", "cease_year", "age", "length_of_service", "dissatisfied"]:
        assert col in df.columns


def test_transform_tafe_maps_length_of_service(raw_tafe):
    df = transform_tafe(clean_tafe(raw_tafe)[0])
    # every non-null length_of_service should be a positive number
    vals = df["length_of_service"].dropna()
    assert (vals > 0).all()
