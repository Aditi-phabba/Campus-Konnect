"""
Campus Konnect - Events Module
Provides event discovery, creation, categorization, search,
and one-click registration tracking.
"""

from datetime import date, time
import streamlit as st
from services.auth import get_current_user, is_admin_user

from services.events import create_event, get_events
from services.recommendations import rank_events_for_user
from components.ui_components import render_page_header, render_empty_state
from components.event_card import render_event_card
from utils.constants import EVENT_CATEGORIES, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_FILE_SIZE_MB
from utils.validators import validate_required_text, validate_file_upload


def render_events_page() -> None:
    """Render the Events discovery and registration page."""
    user = get_current_user()
    current_user_id = user.get("id") if user else None
    is_admin = is_admin_user()

    render_page_header(
        title="Campus Events",
        subtitle="Explore hackathons, technical workshops, guest seminars, and cultural fests.",
        icon="📅"
    )

    # 1. Admin Event Creation (Admins only)
    if is_admin:
        with st.expander("➕ Create Campus Event (Admin)", expanded=False):
            with st.form(key="form_create_event", clear_on_submit=True):

                col_e1, col_e2 = st.columns([2, 1])
                with col_e1:
                    ev_title = st.text_input("Event Name", placeholder="e.g. Annual Campus Hackathon 2026")
                with col_e2:
                    ev_category = st.selectbox("Category", options=EVENT_CATEGORIES)

                ev_desc = st.text_area("Event Description", placeholder="Detail agenda, eligibility, prizes, prerequisites...")

                col_d, col_t1, col_t2 = st.columns(3)
                with col_d:
                    ev_date = st.date_input("Event Date", min_value=date.today())
                with col_t1:
                    ev_start = st.time_input("Start Time", value=time(10, 0))
                with col_t2:
                    ev_end = st.time_input("End Time", value=time(13, 0))

                col_v, col_o = st.columns(2)
                with col_v:
                    ev_venue = st.text_input("Venue", placeholder="Auditorium B / Lab 304 / Online Zoom")
                with col_o:
                    ev_organizer = st.text_input("Organizer", placeholder="e.g. ACM Student Chapter, Placement Cell")

                ev_link = st.text_input("External Registration / Meeting Link (Optional)", placeholder="https://...")
                ev_banner = st.file_uploader("Event Poster / Banner (Optional)", type=ALLOWED_IMAGE_EXTENSIONS)

                submit_ev = st.form_submit_button("Publish Event 🚀", type="primary", use_container_width=True)

                if submit_ev:
                    valid_t, err_t = validate_required_text(ev_title, "Event Name", min_len=3, max_len=200)
                    valid_d, err_d = validate_required_text(ev_desc, "Description", min_len=5, max_len=3000)
                    valid_v, err_v = validate_required_text(ev_venue, "Venue", min_len=2, max_len=200)
                    valid_o, err_o = validate_required_text(ev_organizer, "Organizer", min_len=2, max_len=200)

                    if not valid_t:
                        st.error(err_t)
                    elif not valid_d:
                        st.error(err_d)
                    elif not valid_v:
                        st.error(err_v)
                    elif not valid_o:
                        st.error(err_o)
                    else:
                        img_bytes = None
                        img_name = None
                        img_type = "image/jpeg"
                        img_valid = True

                        if ev_banner:
                            img_valid, img_err = validate_file_upload(
                                ev_banner.name,
                                ev_banner.size,
                                ALLOWED_IMAGE_EXTENSIONS,
                                MAX_IMAGE_FILE_SIZE_MB
                            )
                            if not img_valid:
                                st.error(img_err)
                            else:
                                img_bytes = ev_banner.getvalue()
                                img_name = ev_banner.name
                                img_type = ev_banner.type or "image/jpeg"

                        if img_valid:
                            with st.spinner("Publishing event..."):
                                ok, msg, _ = create_event(
                                    title=ev_title,
                                    description=ev_desc,
                                    category=ev_category,
                                    event_date=str(ev_date),
                                    start_time=str(ev_start),
                                    end_time=str(ev_end),
                                    venue=ev_venue,
                                    organizer=ev_organizer,
                                    created_by=current_user_id,
                                    registration_link=ev_link,
                                    image_bytes=img_bytes,
                                    image_name=img_name,
                                    mime_type=img_type
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

    st.write("")

    # 2. Search & Category Filters
    col_s, col_c = st.columns([2.5, 1.5])
    with col_s:
        search_query = st.text_input("Search Events", placeholder="Search by name, topic, venue...", label_visibility="collapsed")
    with col_c:
        cat_filter = st.selectbox("Category", options=["All Categories"] + EVENT_CATEGORIES, label_visibility="collapsed")

    # 3. Retrieve All Events
    cat_param = cat_filter if cat_filter != "All Categories" else None
    all_events = get_events(
        category=cat_param,
        search_query=search_query,
        current_user_id=current_user_id
    )

    # Smart rank events
    ranked_events = rank_events_for_user(all_events, user)

    # Filter event subsets
    upcoming_events = [e for e in ranked_events if e.get("timeline") == "upcoming"]
    today_events = [e for e in ranked_events if e.get("timeline") == "today"]
    my_events = [e for e in ranked_events if e.get("is_registered")]
    past_events = [e for e in ranked_events if e.get("timeline") == "past"]

    # 4. View Tabs
    tab_upcoming, tab_today, tab_my, tab_past = st.tabs([
        f"🚀 Upcoming ({len(upcoming_events)})",
        f"🔥 Happening Today ({len(today_events)})",
        f"🎟️ My Registrations ({len(my_events)})",
        f"📜 Past Events ({len(past_events)})"
    ])

    with tab_upcoming:
        if not upcoming_events:
            render_empty_state("No upcoming events found", "Check back soon for new campus activities!", "🗓️")
        else:
            for idx, ev in enumerate(upcoming_events):
                render_event_card(ev, current_user_id=current_user_id, context_id=f"up_{idx}")

    with tab_today:
        if not today_events:
            render_empty_state("No events scheduled for today", "Take this time to review study materials or catch up on discussions.", "☕")
        else:
            for idx, ev in enumerate(today_events):
                render_event_card(ev, current_user_id=current_user_id, context_id=f"today_{idx}")

    with tab_my:
        if not current_user_id:
            st.info("Please log in to view your registrations.")
        elif not my_events:
            render_empty_state("You haven't registered for any events yet", "Explore upcoming hackathons and workshops and click 'Register Now'.", "🎟️")
        else:
            for idx, ev in enumerate(my_events):
                render_event_card(ev, current_user_id=current_user_id, context_id=f"myreg_{idx}")

    with tab_past:
        if not past_events:
            render_empty_state("No past events recorded", "Concluded events will be archived here.", "📁")
        else:
            for idx, ev in enumerate(past_events):
                render_event_card(ev, current_user_id=current_user_id, context_id=f"past_{idx}")


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_events_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")

