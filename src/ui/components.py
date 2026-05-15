"""Reusable UI components — KPI cards, section headers, aspect badges."""

import streamlit as st


def kpi_card(
    label: str,
    value: str,
    delta: str | None = None,
    color: str | None = None,
) -> None:
    """Render a glassmorphic KPI card.

    Args:
        label: Card title (e.g. "Total Responses").
        value: Main display value.
        delta: Optional delta string (e.g. "+12%").
        color: Optional override color for the value.
    """
    value_style = f"color: {color};" if color else ""
    delta_html = ""
    if delta is not None:
        if delta.startswith("+"):
            delta_class = "delta-positive"
        elif delta.startswith("-"):
            delta_class = "delta-negative"
        else:
            delta_class = "delta-neutral"
        delta_html = f'<div class="delta {delta_class}">{delta}</div>'

    st.markdown(
        f"""
        <div class="glass-card">
            <h3>{label}</h3>
            <div class="value" style="{value_style}">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    """Render a styled section header.

    Args:
        title: Section title.
        subtitle: Optional description text.
    """
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-header">
            <h2>{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def aspect_badge(aspect: str, sentiment: str) -> str:
    """Return HTML for a colored aspect pill badge.

    Args:
        aspect: Aspect name (e.g. "pricing").
        sentiment: One of "positive", "neutral", "negative".

    Returns:
        HTML string for the badge.
    """
    badge_class = f"badge-{sentiment}"
    display_name = aspect.replace("_", " ").title()
    return f'<span class="aspect-badge {badge_class}">{display_name}</span>'
