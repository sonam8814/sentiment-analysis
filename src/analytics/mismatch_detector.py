"""Mismatch detection — identifies toxic promoters and glowing detractors.

Pure functions — no Streamlit, Supabase, or LLM imports.
"""

import pandas as pd


def flag_toxic_promoters(df: pd.DataFrame) -> pd.DataFrame:
    """Add is_toxic_promoter and is_glowing_detractor columns.

    Toxic promoter: nps_score >= 9 AND overall_sentiment == "negative".
    Glowing detractor: nps_score <= 6 AND overall_sentiment == "positive".

    Args:
        df: DataFrame with 'nps_score' and 'overall_sentiment' columns.

    Returns:
        DataFrame with 'is_toxic_promoter' and 'is_glowing_detractor' columns added.
    """
    df = df.copy()

    if df.empty:
        df["is_toxic_promoter"] = pd.Series(dtype="bool")
        df["is_glowing_detractor"] = pd.Series(dtype="bool")
        return df

    df["is_toxic_promoter"] = (df["nps_score"] >= 9) & (
        df["overall_sentiment"] == "negative"
    )

    df["is_glowing_detractor"] = (df["nps_score"] <= 6) & (
        df["overall_sentiment"] == "positive"
    )

    return df
