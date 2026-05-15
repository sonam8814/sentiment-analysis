"""Sidebar controls — date range, segment filter, refresh, provider indicator."""

from datetime import date, timedelta

import streamlit as st

from config.settings import get_settings


def render_sidebar() -> dict:
    """Render the sidebar and return the current filter state.

    Returns:
        Dict with keys: start_date, end_date, segments, page.
    """
    settings = get_settings()

    with st.sidebar:
        st.markdown("## NPS Analytics")
        st.markdown("---")

        # Date range picker
        st.markdown("### Date Range")
        default_end = date.today()
        default_start = default_end - timedelta(days=30)

        start_date = st.date_input("Start date", value=default_start, key="start_date")
        end_date = st.date_input("End date", value=default_end, key="end_date")

        if start_date > end_date:
            st.error("Start date must be before end date.")
            start_date, end_date = end_date, start_date

        st.markdown("---")

        # Segment filter
        st.markdown("### Segments")
        segment_options = ["enterprise", "smb", "free"]
        segments = st.multiselect(
            "Filter by segment",
            options=segment_options,
            default=segment_options,
            key="segments",
        )

        st.markdown("---")

        # Refresh button
        if st.button("Refresh Data", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # LLM provider indicator
        provider = settings.llm_provider_primary.upper()
        st.markdown(
            f"""
            <div style="text-align: center; padding: 0.5rem;">
                <span style="color: #9CA3AF; font-size: 0.75rem;">LLM PROVIDER</span><br>
                <span style="color: #6366F1; font-weight: 600;">{provider}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Page navigation
        page = st.radio(
            "Navigate",
            options=["Overview", "Aspects", "Toxic Promoters", "Raw Data"],
            key="page_nav",
        )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "segments": segments,
        "page": page,
    }
