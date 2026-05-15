"""Overview page — KPI cards, NPS trend, category donut, top aspects."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.theme import COLORS
from src.analytics.aggregator import aspect_sentiment_distribution, nps_trend
from src.analytics.nps_calculator import calculate_nps, category_breakdown
from src.ui.components import kpi_card, section_header


def _compute_delta(current: float, previous: float) -> str:
    """Format a delta string comparing current vs previous period.

    Args:
        current: Current period value.
        previous: Previous period value.

    Returns:
        Formatted delta string like "+12.3" or "-5.0".
    """
    diff = current - previous
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.1f}"


def _split_periods(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a DataFrame into current and previous halves by response_date.

    Args:
        df: DataFrame with 'response_date' column.

    Returns:
        Tuple of (current_period_df, previous_period_df).
    """
    if df.empty:
        return df, df

    dates = pd.to_datetime(df["response_date"])
    midpoint = dates.min() + (dates.max() - dates.min()) / 2
    current = df[dates >= midpoint]
    previous = df[dates < midpoint]
    return current, previous


def render_overview(df: pd.DataFrame) -> None:
    """Render the Overview page.

    Args:
        df: Processed DataFrame with all derived columns.
    """
    section_header("Overview", "Key NPS metrics at a glance")

    # Split for delta calculations
    current, previous = _split_periods(df)

    nps_current = calculate_nps(current) if not current.empty else 0.0
    nps_previous = calculate_nps(previous) if not previous.empty else 0.0
    breakdown_current = category_breakdown(current)
    breakdown_previous = category_breakdown(previous)

    total_current = len(current)
    total_previous = len(previous)

    # Top row: 4 KPI cards
    cols = st.columns(4)
    with cols[0]:
        kpi_card(
            "Total Responses",
            f"{len(df):,}",
            delta=_compute_delta(total_current, total_previous),
        )
    with cols[1]:
        nps_val = calculate_nps(df)
        nps_color = COLORS["promoter"] if nps_val >= 0 else COLORS["detractor"]
        kpi_card(
            "NPS Score",
            f"{nps_val:+.0f}",
            delta=_compute_delta(nps_current, nps_previous),
            color=nps_color,
        )
    with cols[2]:
        bd = category_breakdown(df)
        pct_promoters = bd["promoter"] * 100
        delta_prom = _compute_delta(
            breakdown_current["promoter"] * 100,
            breakdown_previous["promoter"] * 100,
        )
        kpi_card(
            "% Promoters",
            f"{pct_promoters:.1f}%",
            delta=f"{delta_prom}pp",
            color=COLORS["promoter"],
        )
    with cols[3]:
        pct_detractors = bd["detractor"] * 100
        delta_det = _compute_delta(
            breakdown_current["detractor"] * 100,
            breakdown_previous["detractor"] * 100,
        )
        kpi_card(
            "% Detractors",
            f"{pct_detractors:.1f}%",
            delta=f"{delta_det}pp",
            color=COLORS["detractor"],
        )

    # Middle row: NPS trend + category donut
    section_header("Trends", "NPS over time and category distribution")
    col_trend, col_donut = st.columns([2, 1])

    with col_trend:
        trend_df = nps_trend(df, freq="W")
        if not trend_df.empty:
            trend_df["period_str"] = trend_df["period"].astype(str)
            fig = px.line(
                trend_df,
                x="period_str",
                y="nps",
                markers=True,
                labels={"period_str": "Week", "nps": "NPS Score"},
            )
            fig.update_traces(line_color=COLORS["accent"], line_width=3)
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="",
                yaxis_title="NPS",
                yaxis=dict(range=[-100, 100]),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available for the selected range.")

    with col_donut:
        if not df.empty:
            bd = category_breakdown(df)
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Promoters", "Passives", "Detractors"],
                        values=[bd["promoter"], bd["passive"], bd["detractor"]],
                        hole=0.6,
                        marker_colors=[
                            COLORS["promoter"],
                            COLORS["passive"],
                            COLORS["detractor"],
                        ],
                        textinfo="percent",
                        textfont_size=14,
                    )
                ]
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=30, b=20),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.15, x=0.5, xanchor="center"
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    # Bottom row: Top 5 aspects by volume
    section_header("Top Aspects", "Most mentioned aspects with sentiment breakdown")
    if not df.empty and "aspects" in df.columns:
        aspect_dist = aspect_sentiment_distribution(df)
        if not aspect_dist.empty:
            aspect_dist["total"] = (
                aspect_dist["positive"]
                + aspect_dist["neutral"]
                + aspect_dist["negative"]
            )
            top5 = aspect_dist.nlargest(5, "total")

            fig = go.Figure()
            for sentiment, color in [
                ("positive", COLORS["promoter"]),
                ("neutral", COLORS["passive"]),
                ("negative", COLORS["detractor"]),
            ]:
                fig.add_trace(
                    go.Bar(
                        x=top5["aspect"].str.replace("_", " ").str.title(),
                        y=top5[sentiment],
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
        else:
            st.info("No aspect data available.")
    else:
        st.info("No aspect data available.")
