"""Toxic Promoters page — triage table with CSV export and glowing detractors."""

import pandas as pd
import streamlit as st

from src.ui.components import section_header


def _build_triage_df(df: pd.DataFrame, flag_col: str) -> pd.DataFrame:
    """Build a triage table from flagged rows.

    Args:
        df: Full processed DataFrame.
        flag_col: Boolean column name to filter on.

    Returns:
        Triage DataFrame with display columns.
    """
    if flag_col not in df.columns:
        return pd.DataFrame()

    flagged = df[df[flag_col] == True].copy()  # noqa: E712
    if flagged.empty:
        return pd.DataFrame()

    display = pd.DataFrame(
        {
            "Date": flagged["response_date"],
            "Score": flagged["nps_score"],
            "Comment": flagged["comment_redacted"],
            "Overall Sentiment": flagged["overall_sentiment"],
            "Segment": flagged.get("segment", ""),
        }
    )

    # Format aspects as text
    aspect_strs = []
    for aspects_list in flagged["aspects"]:
        if isinstance(aspects_list, list) and aspects_list:
            parts = [
                f"{a.get('aspect', '').replace('_', ' ')} ({a.get('sentiment', '')})"
                for a in aspects_list
                if isinstance(a, dict)
            ]
            aspect_strs.append(", ".join(parts))
        else:
            aspect_strs.append("")
    display["Aspects"] = aspect_strs

    return display.reset_index(drop=True)


def render_toxic_promoters(df: pd.DataFrame) -> None:
    """Render the Toxic Promoters triage page.

    Args:
        df: Processed DataFrame with mismatch flags.
    """
    section_header(
        "Toxic Promoters",
        "High NPS score (9-10) but negative sentiment — silent churn risk",
    )

    if df.empty:
        st.info("No data available for the selected filters.")
        return

    # Toxic Promoters table
    toxic_df = _build_triage_df(df, "is_toxic_promoter")

    if not toxic_df.empty:
        st.markdown(
            f"**{len(toxic_df)}** toxic promoter(s) found",
        )

        # Search filter
        search = st.text_input(
            "Search comments",
            key="toxic_search",
            placeholder="Type to filter...",
        )
        if search:
            toxic_df = toxic_df[
                toxic_df["Comment"].str.contains(search, case=False, na=False)
            ]

        st.dataframe(
            toxic_df,
            use_container_width=True,
            hide_index=True,
        )

        # CSV export
        csv = toxic_df.to_csv(index=False)
        st.download_button(
            label="Export Toxic Promoters CSV",
            data=csv,
            file_name="toxic_promoters.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.success(
            "No toxic promoters detected — all promoters have matching sentiment."
        )

    # Glowing Detractors section
    st.markdown("---")
    section_header(
        "Glowing Detractors",
        "Low NPS score (0-6) but positive sentiment — potential recovery targets",
    )

    glowing_df = _build_triage_df(df, "is_glowing_detractor")

    if not glowing_df.empty:
        st.markdown(f"**{len(glowing_df)}** glowing detractor(s) found")

        search_glow = st.text_input(
            "Search comments",
            key="glowing_search",
            placeholder="Type to filter...",
        )
        if search_glow:
            glowing_df = glowing_df[
                glowing_df["Comment"].str.contains(search_glow, case=False, na=False)
            ]

        st.dataframe(
            glowing_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_glow = glowing_df.to_csv(index=False)
        st.download_button(
            label="Export Glowing Detractors CSV",
            data=csv_glow,
            file_name="glowing_detractors.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("No glowing detractors detected.")
