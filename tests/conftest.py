"""Shared fixtures for the test suite."""

import json
from pathlib import Path

import pandas as pd
import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_responses_json() -> list[dict]:
    """Load sample NPS responses from the fixtures file."""
    with open(FIXTURES_DIR / "sample_responses.json") as f:
        return json.load(f)


@pytest.fixture
def sample_df(sample_responses_json: list[dict]) -> pd.DataFrame:
    """Return a DataFrame built from sample responses."""
    return pd.DataFrame(sample_responses_json)
