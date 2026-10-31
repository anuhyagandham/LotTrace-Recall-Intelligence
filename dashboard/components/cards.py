"""
KPI Cards and styling components for the LotTrace AI Streamlit Dashboard.
"""

import streamlit as st


def apply_theme():
    """Injects professional enterprise Navy & Slate CSS theme."""
    st.markdown(
        """
        <style>
        .main {
            background-color: #F8FAFC;
        }
        .metric-card {
            background: linear-gradient(135deg, #1E3E62 0%, #0B192C 100%);
            color: #FFFFFF;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
            border-left: 5px solid #008DDA;
        }
        .metric-card-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94A3B8;
            margin-bottom: 5px;
        }
        .metric-card-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #FFFFFF;
        }
        .metric-card-subtitle {
            font-size: 0.8rem;
            color: #38BDF8;
            margin-top: 4px;
        }
        .stButton>button {
            background-color: #1E3E62;
            color: white;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 8px 16px;
        }
        .stButton>button:hover {
            background-color: #008DDA;
            color: white;
        }
        .status-badge-critical {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
        }
        .status-badge-ok {
            background-color: #DCFCE7;
            color: #166534;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(title: str, value: Any, subtitle: str = ""):
    """Renders a styled enterprise KPI card."""
    formatted_val = f"{value:,}" if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-title">{title}</div>
            <div class="metric-card-value">{formatted_val}</div>
            <div class="metric-card-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
