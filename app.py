"""Streamlit entry point — routes to pages, no business logic here."""

import streamlit as st

st.set_page_config(
    page_title="NPS Sentiment Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd  # noqa: E402
from loguru import logger  # noqa: E402

from config.settings import get_settings  # noqa: E402
from src.ai.absa_engine import analyze_dataframe  # noqa: E402
from src.analytics.mismatch_detector import flag_toxic_promoters  # noqa: E402
from src.data.cleaner import clean_dataframe  # noqa: E402
from src.data.supabase_client import fetch_responses  # noqa: E402
from src.ui.components import header_bar  # noqa: E402
from src.ui.pages.aspects import render_aspects  # noqa: E402
from src.ui.pages.overview import render_overview  # noqa: E402
from src.ui.pages.raw_explorer import render_raw_explorer  # noqa: E402
from src.ui.pages.toxic_promoters import render_toxic_promoters  # noqa: E402
from src.ui.sidebar import render_sidebar  # noqa: E402
from src.ui.styles import inject_css  # noqa: E402
from src.utils.logging_config import setup_logging  # noqa: E402


# Initialize logging once
settings = get_settings()
setup_logging(settings.log_level)

# Inject CSS
inject_css()


@st.cache_data(ttl=600, show_spinner=False)
def load_and_process_data(
    start_date: str,
    end_date: str,
) -> tuple[pd.DataFrame, str]:
    """Fetch, clean, analyze, and flag NPS data.

    Cached at the Streamlit layer with 10-minute TTL.
    LLM responses are additionally cached at the disk layer.

    Args:
        start_date: ISO date string for range start.
        end_date: ISO date string for range end.

    Returns:
        Tuple of (processed DataFrame, ISO timestamp of when data was fetched).
    """
    from datetime import date, datetime

    logger.info(f"Loading data: {start_date} to {end_date}")
    fetched_at = datetime.now().isoformat()

    # Fetch from Supabase
    df = fetch_responses(
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
    )

    if df.empty:
        logger.info("No data returned from Supabase")
        return df, fetched_at

    # Clean and redact PII
    df = clean_dataframe(df)

    # Run ABSA (LLM layer has its own disk cache)
    try:
        df = analyze_dataframe(df)
    except Exception as exc:
        logger.error(f"ABSA analysis failed, continuing without it: {exc}")
        df["aspects"] = [[] for _ in range(len(df))]
        df["overall_sentiment"] = "neutral"
        df["analyzed_at"] = pd.Timestamp.now(tz="UTC")

    # Flag mismatches
    df = flag_toxic_promoters(df)

    logger.info(f"Pipeline complete: {len(df)} rows processed")
    return df, fetched_at


def main() -> None:
    """Main application entry point."""
    # Render sidebar and get filter state
    filters = render_sidebar()

    # Load data
    with st.spinner("Loading and analyzing data..."):
        df, fetched_at = load_and_process_data(
            start_date=filters["start_date"].isoformat(),
            end_date=filters["end_date"].isoformat(),
        )

    # Apply segment filter (post-cache, since it's a lightweight filter)
    # Skip when no segment options exist — avoids filtering out all rows
    if not df.empty and "segment" in df.columns and filters["segments"]:
        df = df[df["segment"].isin(filters["segments"])]

    # Header bar with actual data fetch timestamp
    header_bar(fetched_at=fetched_at)

    # Tab navigation
    tab_overview, tab_aspects, tab_toxic, tab_raw = st.tabs(
        ["Overview", "Aspects", "Toxic Promoters", "Raw Data"]
    )

    with tab_overview:
        render_overview(df)
    with tab_aspects:
        render_aspects(df)
    with tab_toxic:
        render_toxic_promoters(df)
    with tab_raw:
        render_raw_explorer(df)


if __name__ == "__main__":
    main()
