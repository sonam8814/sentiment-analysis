"""CSS injection for the Streamlit dashboard."""

import streamlit as st

from config.theme import COLORS


def inject_css() -> None:
    """Inject custom CSS once into the Streamlit app.

    Applies:
    - Inter font from Google Fonts.
    - Glassmorphism card styling.
    - Hidden Streamlit default header/footer.
    - Dark theme consistency.
    """
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global font */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        /* Hide Streamlit default menu and footer, but keep header for sidebar toggle */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{background: transparent !important; border-bottom: none !important;}}

        /* Glassmorphism card */
        .glass-card {{
            background: {COLORS["bg_card"]};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid {COLORS["border"]};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }}

        .glass-card h3 {{
            color: {COLORS["text_secondary"]};
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .glass-card .value {{
            color: {COLORS["text_primary"]};
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
        }}

        .glass-card .delta {{
            font-size: 0.85rem;
            font-weight: 500;
            margin-top: 0.25rem;
        }}

        .delta-positive {{
            color: {COLORS["promoter"]};
        }}

        .delta-negative {{
            color: {COLORS["detractor"]};
        }}

        .delta-neutral {{
            color: {COLORS["text_secondary"]};
        }}

        /* Section headers */
        .section-header {{
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}

        .section-header h2 {{
            color: {COLORS["text_primary"]};
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}

        .section-header p {{
            color: {COLORS["text_secondary"]};
            font-size: 0.875rem;
            margin: 0;
        }}

        /* Aspect badge */
        .aspect-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
            margin-bottom: 0.25rem;
        }}

        .badge-positive {{
            background: rgba(16, 185, 129, 0.15);
            color: {COLORS["promoter"]};
        }}

        .badge-negative {{
            background: rgba(239, 68, 68, 0.15);
            color: {COLORS["detractor"]};
        }}

        .badge-neutral {{
            background: rgba(245, 158, 11, 0.15);
            color: {COLORS["passive"]};
        }}

        /* Header bar */
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid {COLORS["border"]};
        }}

        .header-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {COLORS["text_primary"]};
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .header-title .accent {{
            color: {COLORS["accent"]};
        }}

        .header-timestamp {{
            font-size: 0.75rem;
            color: {COLORS["text_secondary"]};
        }}

        /* Sparkline inside KPI card */
        .glass-card svg.sparkline {{
            display: block;
            margin-top: 0.5rem;
        }}

        /* Empty state */
        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem 1.5rem;
            text-align: center;
        }}

        .empty-state .empty-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            opacity: 0.6;
        }}

        .empty-state .empty-message {{
            color: {COLORS["text_primary"]};
            font-size: 1rem;
            font-weight: 500;
            margin: 0 0 0.25rem 0;
        }}

        .empty-state .empty-suggestion {{
            color: {COLORS["text_secondary"]};
            font-size: 0.85rem;
            margin: 0;
        }}

        /* Sidebar footer badge */
        .sidebar-footer-badge {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.4rem;
            margin-top: 2rem;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            background: {COLORS["bg_card"]};
            border: 1px solid {COLORS["border"]};
            width: fit-content;
            margin-left: auto;
            margin-right: auto;
        }}

        .sidebar-footer-badge .badge-label {{
            font-size: 0.65rem;
            font-weight: 600;
            color: {COLORS["text_secondary"]};
            letter-spacing: 0.05em;
        }}

        .sidebar-footer-badge .badge-value {{
            font-size: 0.7rem;
            font-weight: 700;
            color: {COLORS["accent"]};
        }}

        /* Responsive stacking */
        @media (max-width: 768px) {{
            .glass-card .value {{
                font-size: 1.5rem;
            }}
            .header-bar {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.25rem;
            }}
        }}

        /* Streamlit dataframe styling */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
