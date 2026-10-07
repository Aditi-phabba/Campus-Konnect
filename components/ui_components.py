"""
Campus Konnect - UI Component Library & Design System
Provides custom CSS, headers, metric cards, empty states, and badge styling.
"""

from typing import Any, Optional
import streamlit as st
from utils.helpers import get_category_color, get_badge_props


def inject_custom_css() -> None:
    """Inject polished, modern CSS styling tailored for Campus Konnect."""
    st.markdown(
        """
        <style>
        /* Hide default Streamlit multi-page sidebar navigation */
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        [data-testid="stSidebarNavItems"] {
            display: none !important;
        }

        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Clean app background */
        .stApp {
            background-color: #F8FAFC;
        }

        /* Clean up top header bar spacing */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0;
        }

        /* Cards & Container surfaces */
        .ck-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.25rem;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px 0 rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease-in-out;
        }
        .ck-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
            border-color: #CBD5E1;
        }

        .ck-card-pinned {
            border-left: 4px solid #4F46E5 !important;
            background: #FCFDFF;
        }

        /* Stat Metrics */
        .ck-metric-box {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 1.25rem 1rem;
            border: 1px solid #E2E8F0;
            text-align: center;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        }
        .ck-metric-val {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1E293B;
            line-height: 1.2;
            margin-top: 0.25rem;
        }
        .ck-metric-label {
            font-size: 0.85rem;
            font-weight: 500;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        /* Badge chips */
        .ck-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1;
        }

        /* Smart score badge */
        .ck-smart-tag {
            background: #EEF2FF;
            color: #4338CA;
            border: 1px solid #C7D2FE;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }

        /* Empty states */
        .ck-empty-container {
            background: #FFFFFF;
            border: 2px dashed #E2E8F0;
            border-radius: 12px;
            padding: 3rem 1.5rem;
            text-align: center;
            margin: 1.5rem 0;
        }
        .ck-empty-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
        }
        .ck-empty-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: #334155;
            margin-bottom: 0.25rem;
        }
        .ck-empty-desc {
            font-size: 0.9rem;
            color: #64748B;
            max-width: 450px;
            margin: 0 auto;
        }

        /* Header block */
        .ck-header-wrap {
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #E2E8F0;
        }
        .ck-header-title {
            font-size: 1.85rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.02em;
            margin-bottom: 0.2rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .ck-header-sub {
            font-size: 0.95rem;
            color: #64748B;
            margin-top: 0;
        }

        /* Avatar circle */
        .ck-avatar {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #E2E8F0;
        }
        .ck-avatar-fallback {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: #4F46E5;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.95rem;
        }

        /* Buttons polishing */
        div.stButton > button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.15s ease !important;
        }
        div.stButton > button:hover {
            transform: translateY(-1px);
        }

        /* Tabs polishing */
        button[data-baseweb="tab"] {
            font-weight: 500 !important;
            border-radius: 6px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a consistent, clean page header using native Streamlit."""
    h_title = f"{icon} {title}" if icon else title
    st.markdown(f"## {h_title}")
    if subtitle:
        st.caption(subtitle)
    st.write("")


def render_empty_state(title: str, subtitle: str = "", icon: str = "📭") -> None:
    """Render a well-designed empty state container using native Streamlit."""
    with st.container(border=True):
        st.markdown(f"### {icon}")
        st.markdown(f"**{title}**")
        if subtitle:
            st.caption(subtitle)


def render_metric_card(label: str, value: Any, icon: str = "📊") -> None:
    """Render a clean metric counter box using native Streamlit."""
    with st.container(border=True):
        st.caption(f"{icon} {label}")
        st.markdown(f"### {value}")



def render_category_badge(category: str) -> str:
    """Return a clean native Streamlit markdown badge string (no raw HTML)."""
    cat_label, cat_color = get_badge_props(category)
    return f":{cat_color}-badge[{cat_label}]"
