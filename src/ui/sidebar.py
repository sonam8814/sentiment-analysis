"""Sidebar controls — date range, segment filter, refresh, provider badge."""

from datetime import date, timedelta

import streamlit as st

from config.settings import get_settings
from src.data.supabase_client import fetch_distinct_segments


def render_sidebar() -> dict:
    """Render the sidebar and return the current filter state.

    Returns:
        Dict with keys: start_date, end_date, segments.
    """
    settings = get_settings()

    with st.sidebar:
        st.markdown("## Filters")

        # Date range
        with st.expander("Date Range", expanded=True):
            default_end = date.today()
            default_start = default_end - timedelta(days=30)

            start_date = st.date_input("Start", value=default_start, key="start_date")
            end_date = st.date_input("End", value=default_end, key="end_date")

            if start_date > end_date:
                st.error("Start date must be before end date.")
                start_date, end_date = end_date, start_date

        # Segments
        with st.expander("Segments", expanded=True):
            segment_options = fetch_distinct_segments()
            segments = st.multiselect(
                "Filter by segment",
                options=segment_options,
                default=segment_options,
                key="segments",
                label_visibility="collapsed",
            )

        st.markdown("")

        if st.button("Refresh Data", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        # Provider footer badge
        provider = settings.llm_provider_primary.upper()
        st.markdown(
            f"""
            <div class="sidebar-footer-badge">
                <span class="badge-label">LLM</span>
                <span class="badge-value">{provider}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "segments": segments,
    }
