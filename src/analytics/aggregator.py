"""Time-series and cross-dimensional aggregation functions.

Pure functions — no Streamlit, Supabase, or LLM imports.
"""

import pandas as pd

from src.analytics.nps_calculator import calculate_nps


def nps_trend(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Calculate NPS over time at the given frequency.

    Args:
        df: DataFrame with 'response_date' and 'nps_score' columns.
        freq: Pandas offset alias — "D" (daily), "W" (weekly), "M" (monthly).

    Returns:
        DataFrame with columns ['period', 'nps', 'count'] sorted by period.
        Returns empty DataFrame with those columns if input is empty.
    """
    empty = pd.DataFrame(columns=["period", "nps", "count"])

    if df.empty:
        return empty

    temp = df.copy()
    temp["response_date"] = pd.to_datetime(temp["response_date"])
    temp["period"] = temp["response_date"].dt.to_period(freq)

    rows: list[dict] = []
    for period, group in temp.groupby("period", sort=True):
        rows.append(
            {
                "period": period,
                "nps": calculate_nps(group),
                "count": len(group),
            }
        )

    if not rows:
        return empty

    return pd.DataFrame(rows)


def aspect_sentiment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Count positive/neutral/negative sentiments per aspect.

    Args:
        df: DataFrame with an 'aspects' column (list of dicts with 'aspect' and 'sentiment').

    Returns:
        DataFrame with columns ['aspect', 'positive', 'neutral', 'negative'].
        Returns empty DataFrame with those columns if input is empty.
    """
    columns = ["aspect", "positive", "neutral", "negative"]

    if df.empty or "aspects" not in df.columns:
        return pd.DataFrame(columns=columns)

    records: list[dict] = []
    for aspects_list in df["aspects"]:
        if not isinstance(aspects_list, list):
            continue
        for entry in aspects_list:
            if isinstance(entry, dict) and "aspect" in entry and "sentiment" in entry:
                records.append(
                    {"aspect": entry["aspect"], "sentiment": entry["sentiment"]}
                )

    if not records:
        return pd.DataFrame(columns=columns)

    flat = pd.DataFrame(records)
    pivot = (
        flat.groupby(["aspect", "sentiment"]).size().unstack(fill_value=0).reset_index()
    )

    for col in ["positive", "neutral", "negative"]:
        if col not in pivot.columns:
            pivot[col] = 0

    return pivot[columns]


def aspect_volume_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot aspect counts by segment.

    Args:
        df: DataFrame with 'aspects' (list[dict]) and 'segment' columns.

    Returns:
        DataFrame with 'aspect' as first column and one column per segment.
        Returns empty DataFrame if input is empty.
    """
    if df.empty or "aspects" not in df.columns or "segment" not in df.columns:
        return pd.DataFrame(columns=["aspect"])

    records: list[dict] = []
    for _, row in df.iterrows():
        aspects_list = row.get("aspects", [])
        segment = row.get("segment", "unknown")
        if not isinstance(aspects_list, list):
            continue
        for entry in aspects_list:
            if isinstance(entry, dict) and "aspect" in entry:
                records.append({"aspect": entry["aspect"], "segment": segment})

    if not records:
        return pd.DataFrame(columns=["aspect"])

    flat = pd.DataFrame(records)
    pivot = (
        flat.groupby(["aspect", "segment"]).size().unstack(fill_value=0).reset_index()
    )

    return pivot
