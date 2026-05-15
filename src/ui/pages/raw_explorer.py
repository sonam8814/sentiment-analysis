"""Raw Data Explorer page — full DataFrame view with filters, search, pagination, CSV export."""

import pandas as pd
import streamlit as st

from src.ui.components import section_header

ROWS_PER_PAGE = 50


def render_raw_explorer(df: pd.DataFrame) -> None:
    """Render the Raw Data Explorer page.

    Args:
        df: Processed DataFrame with all derived columns.
    """
    section_header("Raw Data Explorer", "Browse and export all processed responses")

    if df.empty:
        st.info("No data available for the selected filters.")
        return

    # Build display DataFrame (only redacted comments, never raw)
    display_cols = [
        "response_date",
        "nps_score",
        "category",
        "comment_redacted",
        "overall_sentiment",
        "segment",
        "is_toxic_promoter",
        "is_glowing_detractor",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    display_df = df[available_cols].copy()

    # Column filters
    col1, col2, col3 = st.columns(3)
    with col1:
        categories = st.multiselect(
            "Category",
            options=["promoter", "passive", "detractor"],
            default=["promoter", "passive", "detractor"],
            key="raw_category",
        )
    with col2:
        sentiments = st.multiselect(
            "Sentiment",
            options=["positive", "neutral", "negative"],
            default=["positive", "neutral", "negative"],
            key="raw_sentiment",
        )
    with col3:
        search_term = st.text_input(
            "Search comments",
            key="raw_search",
            placeholder="Type to filter...",
        )

    # Apply filters
    if "category" in display_df.columns:
        display_df = display_df[display_df["category"].isin(categories)]
    if "overall_sentiment" in display_df.columns:
        display_df = display_df[display_df["overall_sentiment"].isin(sentiments)]
    if search_term and "comment_redacted" in display_df.columns:
        display_df = display_df[
            display_df["comment_redacted"].str.contains(
                search_term, case=False, na=False
            )
        ]

    # Stats
    st.markdown(f"**{len(display_df):,}** rows matching filters")

    # Pagination
    total_pages = max(1, (len(display_df) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
        key="raw_page",
    )

    start_idx = (page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    page_df = display_df.iloc[start_idx:end_idx]

    st.dataframe(page_df, use_container_width=True, hide_index=True)
    st.caption(f"Page {page} of {total_pages}")

    # CSV export (all filtered rows, not just current page)
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Export Filtered Data CSV",
        data=csv,
        file_name="nps_raw_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
