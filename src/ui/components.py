"""Reusable UI components — KPI cards, section headers, aspect badges, empty states."""

import re
from datetime import datetime

import streamlit as st

from config.theme import COLORS


def _sparkline_svg(
    data: list[float],
    color: str,
    label: str,
    width: int = 80,
    height: int = 24,
) -> str:
    if not data or len(data) < 2:
        return ""

    min_val = min(data)
    max_val = max(data)
    val_range = max_val - min_val or 1
    pad = 2

    points = []
    for i, val in enumerate(data):
        x = pad + (i / (len(data) - 1)) * (width - 2 * pad)
        y = pad + (height - 2 * pad) - ((val - min_val) / val_range) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")

    polyline_pts = " ".join(points)
    fill_pts = f"{pad},{height - pad} {polyline_pts} {width - pad},{height - pad}"
    grad_id = f"sg-{re.sub(r'[^a-z0-9]', '', label.lower())}"

    return (
        f'<svg class="sparkline" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{fill_pts}" fill="url(#{grad_id})"/>'
        f'<polyline points="{polyline_pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


def kpi_card(
    label: str,
    value: str,
    delta: str | None = None,
    color: str | None = None,
    sparkline: list[float] | None = None,
) -> None:
    """Render a glassmorphic KPI card with optional sparkline."""
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

    spark_color = color or COLORS["accent"]
    spark_html = _sparkline_svg(sparkline, spark_color, label) if sparkline else ""

    st.markdown(
        f"""
        <div class="glass-card">
            <h3>{label}</h3>
            <div class="value" style="{value_style}">{value}</div>
            {delta_html}
            {spark_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def header_bar() -> None:
    """Render the branded header bar with app title and refresh timestamp."""
    now = datetime.now().strftime("%b %d, %Y %I:%M %p")
    st.markdown(
        f"""
        <div class="header-bar">
            <div class="header-title">
                <span class="accent">NPS</span> Sentiment Analytics
            </div>
            <div class="header-timestamp">Last refreshed &middot; {now}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(
    icon: str,
    message: str,
    suggestion: str | None = None,
) -> None:
    """Render a styled empty-state placeholder."""
    suggestion_html = (
        f'<p class="empty-suggestion">{suggestion}</p>' if suggestion else ""
    )
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <p class="empty-message">{message}</p>
            {suggestion_html}
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
