"""NPS score calculation and category classification.

Pure functions — no Streamlit, Supabase, or LLM imports.
"""

from typing import Literal

import pandas as pd


def categorize(score: int) -> Literal["promoter", "passive", "detractor"]:
    """Classify an NPS score into its category.

    Args:
        score: NPS score (0-10).

    Returns:
        One of "promoter", "passive", or "detractor".
    """
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "passive"
    else:
        return "detractor"


def calculate_nps(df: pd.DataFrame) -> float:
    """Calculate the Net Promoter Score from a DataFrame.

    NPS = %promoters - %detractors, ranging from -100 to +100.

    Args:
        df: DataFrame with an 'nps_score' column (int, 0-10).

    Returns:
        NPS score as a float. Returns 0.0 for empty DataFrames.
    """
    if df.empty:
        return 0.0

    categories = df["nps_score"].apply(categorize)
    total = len(categories)
    promoters = (categories == "promoter").sum()
    detractors = (categories == "detractor").sum()

    return ((promoters - detractors) / total) * 100


def category_breakdown(df: pd.DataFrame) -> dict[str, float]:
    """Return the proportion of each NPS category.

    Args:
        df: DataFrame with an 'nps_score' column.

    Returns:
        Dict with keys "promoter", "passive", "detractor" and float proportions
        summing to 1.0. Returns all zeros for empty DataFrames.
    """
    if df.empty:
        return {"promoter": 0.0, "passive": 0.0, "detractor": 0.0}

    categories = df["nps_score"].apply(categorize)
    total = len(categories)
    counts = categories.value_counts()

    return {
        "promoter": counts.get("promoter", 0) / total,
        "passive": counts.get("passive", 0) / total,
        "detractor": counts.get("detractor", 0) / total,
    }
