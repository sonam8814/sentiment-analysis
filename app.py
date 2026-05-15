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


@st.cache_data(ttl=600)
def load_and_process_data(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch, clean, analyze, and flag NPS data.

    Cached at the Streamlit layer with 10-minute TTL.
    LLM responses are additionally cached at the disk layer.

    Args:
        start_date: ISO date string for range start.
        end_date: ISO date string for range end.

    Returns:
        Fully processed DataFrame.
    """
    from datetime import date

    logger.info(f"Loading data: {start_date} to {end_date}")

    # Fetch from Supabase
    df = fetch_responses(
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
    )

    if df.empty:
        logger.info("No data returned from Supabase")
        return df

    # Clean and redact PII
    df = clean_dataframe(df)

    # Run ABSA (LLM layer has its own disk cache)
    df = analyze_dataframe(df)

    # Flag mismatches
    df = flag_toxic_promoters(df)

    logger.info(f"Pipeline complete: {len(df)} rows processed")
    return df


def main() -> None:
    """Main application entry point."""
    # Render sidebar and get filter state
    filters = render_sidebar()

    # Load data
    df = load_and_process_data(
        start_date=filters["start_date"].isoformat(),
        end_date=filters["end_date"].isoformat(),
    )

    # Apply segment filter (post-cache, since it's a lightweight filter)
    if not df.empty and "segment" in df.columns and filters["segments"]:
        df = df[df["segment"].isin(filters["segments"])]

    # Route to selected page
    page = filters["page"]

    if page == "Overview":
        render_overview(df)
    elif page == "Aspects":
        render_aspects(df)
    elif page == "Toxic Promoters":
        render_toxic_promoters(df)
    elif page == "Raw Data":
        render_raw_explorer(df)


if __name__ == "__main__":
    main()
