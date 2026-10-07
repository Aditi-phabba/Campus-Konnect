"""
Campus Konnect - Main Application Entrypoint
Tagline: "One Campus. One Community. One Connected Platform."

This file acts as the primary controller for the Campus Konnect MVP:
- Page configuration & visual design system initialization
- Supabase connection verification & environment setup wizard
- Authentication gating (Landing / Login / Registration)
- Session state management and multi-page routing
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

from services.database import is_supabase_configured, get_supabase_client
from services.auth import sign_in, sign_up, is_authenticated, get_current_user
from components.ui_components import inject_custom_css
from components.sidebar import render_sidebar
from utils.constants import (
    APP_NAME,
    APP_TAGLINE,
    APP_DESCRIPTION,
    DEPARTMENTS,
    YEARS,
    INTEREST_OPTIONS
)
from utils.validators import (
    validate_email,
    validate_passwords_match,
    validate_required_text
)

# Page Views
from pages.home import render_home_page
from pages.feed import render_feed_page
from pages.events import render_events_page
from pages.resources import render_resources_page
from pages.discussions import render_discussions_page
from pages.profile import render_profile_page
from pages.admin import render_admin_page

# Configure Streamlit page attributes
st.set_page_config(
    page_title=f"{APP_NAME} - Campus Digital Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply bespoke modern UI styling
inject_custom_css()


def render_setup_wizard() -> None:
    """
    Renders an informative, user-friendly setup wizard if Supabase credentials
    are not yet configured in .env or Streamlit secrets.
    """
    with st.container(border=True):
        st.markdown(f"## 🎓 {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.markdown("---")
        st.markdown("### ⚙️ Welcome! Supabase Configuration Required")
        st.markdown(
            "Campus Konnect requires your Supabase Project URL and Anon API key to authenticate students, "
            "store posts, and share academic files."
        )

    with st.container():
        st.markdown("#### 🚀 Quick 3-Step Setup Guide:")
        step1, step2, step3 = st.columns(3)
        with step1:
            st.markdown(
                """
                **1. Create Supabase Project**
                - Go to [supabase.com](https://supabase.com)
                - Create a free project
                - Navigate to Project Settings -> API
                """
            )
        with step2:
            st.markdown(
                """
                **2. Execute Database Schema**
                - Open SQL Editor in Supabase
                - Copy contents of `supabase/schema.sql`
                - Click **Run** to generate tables & RLS
                """
            )
        with step3:
            st.markdown(
                """
                **3. Connect Environment**
                - Add credentials to `.env` file:
                `SUPABASE_URL=...`
                `SUPABASE_KEY=...`
                """
            )

        st.markdown("---")
        st.markdown("##### Or Connect Temporarily from this Browser:")
        with st.form(key="form_temp_setup"):
            input_url = st.text_input("Supabase Project URL", placeholder="https://xyzcompany.supabase.co")
            input_key = st.text_input("Supabase Anon API Key", type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            save_to_env = st.checkbox("Also save credentials to local .env file", value=True)
            submit_setup = st.form_submit_button("Connect to Supabase 🔌", type="primary")

            if submit_setup:
                if not input_url or not input_key:
                    st.error("Please provide both Supabase URL and Anon Key.")
                else:
                    os.environ["SUPABASE_URL"] = input_url.strip()
                    os.environ["SUPABASE_KEY"] = input_key.strip()

                    if save_to_env:
                        try:
                            with open(".env", "w", encoding="utf-8") as f:
                                f.write(f"SUPABASE_URL={input_url.strip()}\n")
                                f.write(f"SUPABASE_KEY={input_key.strip()}\n")
                        except Exception as e:
                            st.warning(f"Could not write .env file directly: {e}")

                    # Clear cached client
                    st.cache_resource.clear()
                    st.success("Credentials saved! Reloading application...")
                    st.rerun()


def render_auth_landing() -> None:
    """
    Renders the modern Landing & Authentication portal (Sign In / Register).
    """
    col_lead1, col_lead2, col_lead3 = st.columns([1, 2, 1])
    with col_lead2:
        st.markdown(f"# 🎓 {APP_NAME}")
        st.markdown(f"**{APP_TAGLINE}**")
        st.caption(APP_DESCRIPTION)
        st.write("")

    auth_col1, auth_col2, auth_col3 = st.columns([1, 2.2, 1])
    with auth_col2:
        tab_login, tab_register = st.tabs(["🔐 Sign In to Campus", "📝 Create Student Account"])

        # -------------------------------------------------------------
        # Tab 1: Login Form
        # -------------------------------------------------------------
        with tab_login:
            st.write("")
            with st.form(key="form_user_login"):
                login_email = st.text_input("College Email", placeholder="student@college.edu")
                login_password = st.text_input("Password", type="password", placeholder="••••••••")

                submit_login = st.form_submit_button("Sign In 🚪", type="primary", use_container_width=True)

                if submit_login:
                    v_email, err_e = validate_email(login_email)
                    if not v_email:
                        st.error(err_e)
                    elif not login_password:
                        st.error("Please enter your password.")
                    else:
                        with st.spinner("Verifying credentials..."):
                            ok, msg, _ = sign_in(login_email, login_password)
                            if ok:
                                st.success("Signed in successfully!")
                                st.rerun()
                            else:
                                st.error(msg)

            st.caption("🔒 Verified campus authentication via Supabase Auth.")

        # -------------------------------------------------------------
        # Tab 2: Registration Form
        # -------------------------------------------------------------
        with tab_register:
            st.write("")
            with st.form(key="form_user_register"):
                reg_name = st.text_input("Full Name", placeholder="e.g. Aditi Sharma")
                reg_email = st.text_input("College Email", placeholder="e.g. aditi.sharma@college.edu")

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    reg_pass = st.text_input("Password", type="password", placeholder="Min 6 characters")
                with col_p2:
                    reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                col_dept, col_year = st.columns([2, 1])
                with col_dept:
                    reg_dept = st.selectbox("Department", options=DEPARTMENTS)
                with col_year:
                    reg_year = st.selectbox("Academic Year", options=YEARS, format_func=lambda y: f"Year {y}")

                reg_interests = st.multiselect(
                    "Academic & Technical Interests",
                    options=INTEREST_OPTIONS,
                    help="Used to personalize your Smart Campus Feed"
                )

                reg_bio = st.text_input("Short Bio (Optional)", placeholder="e.g. 3rd year CSE student interested in AI and hackathons")

                submit_reg = st.form_submit_button("Create Account 🚀", type="primary", use_container_width=True)

                if submit_reg:
                    v_name, err_name = validate_required_text(reg_name, "Full Name", min_len=2, max_len=100)
                    v_email, err_email = validate_email(reg_email)
                    v_pass, err_pass = validate_passwords_match(reg_pass, reg_confirm)

                    if not v_name:
                        st.error(err_name)
                    elif not v_email:
                        st.error(err_email)
                    elif not v_pass:
                        st.error(err_pass)
                    else:
                        with st.spinner("Registering your campus account..."):
                            ok, msg, _ = sign_up(
                                email=reg_email,
                                password=reg_pass,
                                full_name=reg_name,
                                department=reg_dept,
                                year=reg_year,
                                interests=reg_interests,
                                bio=reg_bio
                            )
                            if ok:
                                st.success(msg)
                                st.info("You can now switch to the 'Sign In' tab to log into your account.")
                            else:
                                st.error(msg)


def main() -> None:
    """Main routing controller."""
    # 1. Check if Supabase connection credentials exist
    if not is_supabase_configured():
        render_setup_wizard()
        return

    # 2. Check if user is authenticated
    if not is_authenticated():
        render_auth_landing()
        return

    # 3. Render authenticated application shell with sidebar navigation
    active_page = render_sidebar()

    # Route to designated view
    if active_page == "home":
        render_home_page()
    elif active_page == "feed":
        render_feed_page()
    elif active_page == "events":
        render_events_page()
    elif active_page == "resources":
        render_resources_page()
    elif active_page == "discussions":
        render_discussions_page()
    elif active_page == "profile":
        render_profile_page()
    elif active_page == "admin":
        render_admin_page()
    else:
        render_home_page()


if __name__ == "__main__":
    main()
