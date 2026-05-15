"""Data cleaning and normalization for NPS responses."""

from typing import Literal

import pandas as pd
from loguru import logger

from src.data.pii_redactor import redact


def categorize_score(score: int) -> Literal["promoter", "passive", "detractor"]:
    """Classify an NPS score into its category.

    Args:
        score: NPS score (0-10).

    Returns:
        Category string.
    """
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "passive"
    else:
        return "detractor"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize an NPS response DataFrame.

    Operations:
    - Strips whitespace from string columns.
    - Replaces null comments with empty string.
    - Drops rows with invalid NPS scores (outside 0-10).
    - Adds 'category' column (promoter/passive/detractor).
    - Adds 'comment_redacted' column with PII stripped.

    Args:
        df: Raw DataFrame from Supabase.

    Returns:
        Cleaned DataFrame with derived columns.
    """
    if df.empty:
        df["category"] = pd.Series(dtype="str")
        df["comment_redacted"] = pd.Series(dtype="str")
        logger.info("Empty DataFrame received — returning with added columns")
        return df

    df = df.copy()

    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().replace("nan", "")

    # Replace null/NaN comments with empty string
    df["comment"] = df["comment"].fillna("").astype(str).str.strip()

    # Drop rows with invalid NPS scores
    initial_len = len(df)
    df["nps_score"] = pd.to_numeric(df["nps_score"], errors="coerce")
    df = df.dropna(subset=["nps_score"])
    df["nps_score"] = df["nps_score"].astype(int)
    df = df[(df["nps_score"] >= 0) & (df["nps_score"] <= 10)]
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with invalid NPS scores")

    # Add category column
    df["category"] = df["nps_score"].apply(categorize_score)

    # Add redacted comment column
    df["comment_redacted"] = df["comment"].apply(lambda c: redact(c) if c else "")

    logger.info(
        f"Cleaned DataFrame: {len(df)} rows, "
        f"categories: {df['category'].value_counts().to_dict()}"
    )

    return df.reset_index(drop=True)
