"""Aspects page — stacked bar chart, heatmap, filterable comment list."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.theme import COLORS
from src.analytics.aggregator import (
    aspect_sentiment_distribution,
    aspect_volume_by_segment,
)
from src.ui.components import aspect_badge, section_header


def render_aspects(df: pd.DataFrame) -> None:
    """Render the Aspects analysis page.

    Args:
        df: Processed DataFrame with 'aspects' and 'segment' columns.
    """
    section_header("Aspect Analysis", "Sentiment breakdown by product aspect")

    if df.empty or "aspects" not in df.columns:
        st.info("No aspect data available for the selected filters.")
        return

    # Stacked bar chart: aspect x sentiment
    aspect_dist = aspect_sentiment_distribution(df)
    if not aspect_dist.empty:
        fig = go.Figure()
        for sentiment, color in [
            ("positive", COLORS["promoter"]),
            ("neutral", COLORS["passive"]),
            ("negative", COLORS["detractor"]),
        ]:
            fig.add_trace(
                go.Bar(
                    x=aspect_dist["aspect"].str.replace("_", " ").str.title(),
                    y=aspect_dist[sentiment],
                    name=sentiment.title(),
                    marker_color=color,
                )
            )
        fig.update_layout(
            barmode="stack",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title="",
            yaxis_title="Count",
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center"
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Heatmap: aspect x segment
    section_header("Aspect Volume by Segment")
    if "segment" in df.columns:
        volume_df = aspect_volume_by_segment(df)
        if not volume_df.empty and len(volume_df.columns) > 1:
            segment_cols = [c for c in volume_df.columns if c != "aspect"]
            z_values = volume_df[segment_cols].values.tolist()
            aspects_display = (
                volume_df["aspect"].str.replace("_", " ").str.title().tolist()
            )

            fig = go.Figure(
                data=go.Heatmap(
                    z=z_values,
                    x=segment_cols,
                    y=aspects_display,
                    colorscale=[
                        [0, "rgba(99, 102, 241, 0.1)"],
                        [1, COLORS["accent"]],
                    ],
                    texttemplate="%{z}",
                    textfont={"size": 14},
                )
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="Segment",
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No segment data available for heatmap.")

    # Filterable comment list per aspect
    section_header("Comments by Aspect", "Filter to explore individual feedback")

    all_aspects = set()
    for aspects_list in df["aspects"]:
        if isinstance(aspects_list, list):
            for entry in aspects_list:
                if isinstance(entry, dict) and "aspect" in entry:
                    all_aspects.add(entry["aspect"])

    if not all_aspects:
        st.info("No aspects found in the data.")
        return

    sorted_aspects = sorted(all_aspects)
    selected_aspect = st.selectbox(
        "Select aspect",
        options=sorted_aspects,
        format_func=lambda x: x.replace("_", " ").title(),
    )

    # Filter rows containing the selected aspect
    filtered_rows = []
    for _, row in df.iterrows():
        aspects_list = row.get("aspects", [])
        if not isinstance(aspects_list, list):
            continue
        for entry in aspects_list:
            if isinstance(entry, dict) and entry.get("aspect") == selected_aspect:
                filtered_rows.append(
                    {
                        "Comment": row.get("comment_redacted", ""),
                        "Score": row.get("nps_score", ""),
                        "Sentiment": entry.get("sentiment", ""),
                        "Confidence": f"{entry.get('confidence', 0):.2f}",
                        "Segment": row.get("segment", ""),
                        "Date": row.get("response_date", ""),
                    }
                )

    if filtered_rows:
        # Show badges
        sentiments = [r["Sentiment"] for r in filtered_rows]
        badges_html = ""
        for s in ["positive", "neutral", "negative"]:
            count = sentiments.count(s)
            if count > 0:
                badges_html += aspect_badge(f"{s} ({count})", s)
        st.markdown(badges_html, unsafe_allow_html=True)

        st.dataframe(
            pd.DataFrame(filtered_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f"No comments found for aspect '{selected_aspect}'.")
