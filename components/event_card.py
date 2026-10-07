"""
Campus Konnect - Event Card Component
Renders event cards with schedule details, registration actions, attendee counts,
and organizer information using native Streamlit containers and badges.
All interactive widgets use unique, context-aware keys to prevent StreamlitDuplicateElementKey.
"""

from typing import Dict, Any, Optional
import streamlit as st
from utils.helpers import format_date_str, format_time_str, clean_text, get_badge_props
from services.events import register_for_event, cancel_event_registration, delete_event
from services.auth import is_admin_user


def render_event_card(
    event: Dict[str, Any],
    current_user_id: Optional[str] = None,
    context_id: str = "events"
) -> None:
    """Render a modern event card with registration trigger."""
    event_id = event["id"]
    title = clean_text(event.get("title", ""))
    description = clean_text(event.get("description", ""))
    category = clean_text(event.get("category", "Other"))
    event_date = format_date_str(event.get("event_date"))
    start_time = format_time_str(event.get("start_time"))
    end_time = format_time_str(event.get("end_time"))
    venue = clean_text(event.get("venue", "Campus"))
    organizer = clean_text(event.get("organizer", "College Organization"))
    registration_link = event.get("registration_link", "")
    image_url = event.get("image_url", "")

    reg_count = event.get("registration_count", 0)
    is_registered = event.get("is_registered", False)
    timeline = event.get("timeline", "upcoming")
    raw_smart_score = event.get("_smart_score", None)
    smart_score = 0.0
    if isinstance(raw_smart_score, (int, float)):
        smart_score = float(raw_smart_score)
    elif isinstance(raw_smart_score, str):
        try:
            smart_score = float(raw_smart_score)
        except ValueError:
            smart_score = 0.0

    is_admin = is_admin_user()

    with st.container(border=True):
        # 1. Header Badges & Registrations Counter
        col_meta1, col_meta2 = st.columns([3, 1])
        with col_meta1:
            badges = []
            cat_label, cat_color = get_badge_props(category)
            badges.append((cat_label, cat_color))

            if timeline == "today":
                badges.append(("🔥 Happening Today", "orange"))
            elif timeline == "past":
                badges.append(("Past Event", "gray"))
            else:
                badges.append(("Upcoming", "green"))

            if smart_score > 0:
                score_disp = int(smart_score) if smart_score.is_integer() else smart_score
                badges.append((f"⚡ Match +{score_disp}", "violet"))

            if badges:
                badge_md = " ".join([f":{b_color}-badge[{b_label}]" for b_label, b_color in badges])
                st.markdown(badge_md)

        with col_meta2:
            st.caption(f"👥 **{reg_count}** Registered")

        # 2. Event Title
        st.markdown(f"### {title}")

        # 3. Schedule, Venue & Organizer Details
        col_sch1, col_sch2 = st.columns(2)
        with col_sch1:
            st.markdown(f"📅 **Date:** {event_date}")
            st.markdown(f"⏰ **Time:** {start_time} - {end_time}")
        with col_sch2:
            st.markdown(f"📍 **Venue:** {venue}")
            st.markdown(f"🏢 **Organizer:** {organizer}")

        # 4. Description
        if description:
            st.markdown(description)

        # 5. Image Attachment if present
        if image_url:
            st.image(image_url, use_container_width=True)

        st.markdown("---")

        # 6. Action Buttons
        col_act1, col_act2, col_act3 = st.columns([1.5, 1.5, 2])

        with col_act1:
            if current_user_id:
                if is_registered:
                    if st.button("Cancel Registration", key=f"cancel_reg_{event_id}_{context_id}", type="secondary"):
                        ok, msg = cancel_event_registration(event_id, current_user_id)
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if timeline != "past":
                        if st.button("Register Now", key=f"reg_btn_{event_id}_{context_id}", type="primary"):
                            ok, msg = register_for_event(event_id, current_user_id)
                            if ok:
                                st.toast(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.caption("Event concluded")
            else:
                st.caption("Sign in to register")

        with col_act2:
            if registration_link:
                st.link_button("External Portal 🔗", registration_link, key=f"link_reg_{event_id}_{context_id}", use_container_width=True)

        with col_act3:
            if is_admin:
                if st.button("🗑️ Delete Event (Admin)", key=f"del_ev_{event_id}_{context_id}", type="secondary"):
                    ok, msg = delete_event(event_id, current_user_id or "", is_admin=is_admin)
                    if ok:
                        st.toast("Event removed.")
                        st.rerun()
                    else:
                        st.error(msg)
