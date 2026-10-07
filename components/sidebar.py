"""
Campus Konnect - Sidebar Navigation Component
Renders the brand identity, user profile summary, navigation links, and logout control.
"""

import streamlit as st
from services.auth import get_current_user, is_admin_user, sign_out
from utils.constants import APP_NAME, APP_TAGLINE, YEAR_LABELS


def render_sidebar() -> str:
    """
    Renders the custom sidebar and returns the selected navigation page key.
    """
    user = get_current_user()
    is_admin = is_admin_user()

    with st.sidebar:
        # Branding Header
        st.markdown(f"### 🎓 {APP_NAME}")
        st.caption("Campus Digital Platform")
        st.markdown("---")

        # Logged-in User Profile Summary Card
        if user:
            name = user.get("full_name", "Student")
            dept = user.get("department", "Engineering")
            year = user.get("year", 1)
            year_text = YEAR_LABELS.get(year, f"Year {year}")
            role = user.get("role", "student")

            with st.container(border=True):
                col_u1, col_u2 = st.columns([1.8, 1.2])
                with col_u1:
                    st.markdown(f"**{name}**")
                with col_u2:
                    if role == "admin":
                        st.markdown(":orange-badge[ADMIN]")
                    else:
                        st.markdown(":blue-badge[STUDENT]")
                st.caption(f"{dept} • {year_text}")

        # Navigation Options
        pages = [
            ("🏠 Home", "home"),
            ("📰 Feed", "feed"),
            ("📅 Events", "events"),
            ("📚 Resources", "resources"),
            ("💬 Discussions", "discussions"),
            ("👤 Profile", "profile"),
        ]

        if is_admin:
            pages.append(("🛠️ Admin Dashboard", "admin"))

        # Determine currently selected page
        if "active_page" not in st.session_state:
            st.session_state["active_page"] = "home"

        current_page_idx = 0
        page_keys = [p[1] for p in pages]
        page_labels = [p[0] for p in pages]

        if st.session_state["active_page"] in page_keys:
            current_page_idx = page_keys.index(st.session_state["active_page"])

        selected_label = st.radio(
            "Navigation",
            options=page_labels,
            index=current_page_idx,
            label_visibility="collapsed"
        )

        selected_key = page_keys[page_labels.index(selected_label)]
        st.session_state["active_page"] = selected_key

        st.write("")
        st.markdown("---")

        # System info & Sign Out
        col_out1, col_out2 = st.columns([1, 1])
        with col_out1:
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                sign_out()
                st.rerun()

        with col_out2:
            st.caption("🟢 Online")

        st.caption(f"{APP_NAME} v1.0 • Streamlit & Supabase")

    return st.session_state["active_page"]
