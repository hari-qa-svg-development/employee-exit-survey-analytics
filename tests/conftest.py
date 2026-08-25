"""Shared pytest fixtures for the exit-survey test suite."""

from __future__ import annotations

import pandas as pd
import pytest

import src.config as cfg
from src.clean import clean_dete, clean_tafe
from src.combine import combine_datasets
from src.load import load_dete, load_tafe
from src.transform import transform_dete, transform_tafe


@pytest.fixture(scope="session")
def raw_dete():
    return load_dete()


@pytest.fixture(scope="session")
def raw_tafe():
    return load_tafe()


@pytest.fixture(scope="session")
def dete_clean(raw_dete):
    return clean_dete(raw_dete)[0]


@pytest.fixture(scope="session")
def tafe_clean(raw_tafe):
    return clean_tafe(raw_tafe)[0]


@pytest.fixture(scope="session")
def dete_transformed(dete_clean):
    return transform_dete(dete_clean)


@pytest.fixture(scope="session")
def tafe_transformed(tafe_clean):
    return transform_tafe(tafe_clean)


@pytest.fixture(scope="session")
def combined(dete_transformed, tafe_transformed):
    return combine_datasets(dete_transformed, tafe_transformed)


@pytest.fixture
def tiny_dete():
    """A tiny hand-built DETE frame for unit testing transform rules."""
    return pd.DataFrame(
        {
            "ID": ["1", "2", "3"],
            "SeparationType": ["Resignation", "Resignation", "Retirement"],
            "Cease Date": ["2013/05/22", "2012/11", "2014/01/05"],
            "DETE Start Date": ["2005/03", "2010/02/10", "2009/06/06"],
            "Employment Status": ["Permanent", "Casual", "Permanent"],
            "Age": ["31-35", "56 or older", "Not Stated"],
            "Contributing Factors - Career": ["-", "Career Move", "-"],
            "Contributing Factors - Family": ["-", "-", "-"],
            "Contributing Factors - Maternity": ["-", "-", "-"],
            "Contributing Factors - None": ["-", "-", "-"],
        }
    )
