"""
Campus Konnect - Administrator Control Panel
Provides high-level platform statistics, user management & role elevation,
official campus announcement broadcast, and content moderation.
"""

from datetime import date, time
import streamlit as st
import pandas as pd
from services.auth import get_current_user, is_admin_user
from services.admin import (
    get_admin_dashboard_metrics,
    get_all_users,
    update_user_role,
    publish_official_announcement
)
from services.posts import get_posts, delete_post
from services.events import get_events, create_event, delete_event, get_event_attendees
from services.resources import get_resources, delete_resource
from components.ui_components import render_page_header, render_metric_card, render_empty_state
from utils.constants import EVENT_CATEGORIES, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_FILE_SIZE_MB
from utils.validators import validate_required_text, validate_file_upload
from utils.helpers import format_date_str, clean_text


def render_admin_page() -> None:
    """Render the administrator control dashboard."""
    user = get_current_user()
    if not user or not is_admin_user():
        st.error("⛔ Access Denied: You do not have administrator permissions.")
        st.info(
            "To assign the administrator role during your project demonstration, "
            "run the SQL command documented in README.md / supabase/schema.sql in your Supabase SQL Editor:"
        )
        st.code("UPDATE public.profiles SET role = 'admin' WHERE email = 'your-email@college.edu';", language="sql")
        return

    admin_id = user["id"]

    render_page_header(
        title="Admin Control Center",
        subtitle="Campus Konnect platform administration, user directory, and community governance.",
        icon="🛠️"
    )

    # 1. System Metrics Row
    metrics = get_admin_dashboard_metrics()
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        render_metric_card("Students", metrics["total_users"], "👥")
    with m2:
        render_metric_card("Posts", metrics["total_posts"], "📝")
    with m3:
        render_metric_card("Events", metrics["total_events"], "📅")
    with m4:
        render_metric_card("Resources", metrics["total_resources"], "📚")
    with m5:
        render_metric_card("Discussions", metrics["total_discussions"], "💬")
    with m6:
        render_metric_card("Registrations", metrics["total_registrations"], "🎟️")

    st.write("")

    # 2. Administrative Action Tabs
    tab_announcements, tab_users, tab_posts, tab_events, tab_resources = st.tabs([
        "📢 Create Official Announcement",
        "👥 User Directory",
        "📝 Post Moderation",
        "📅 Event Management",
        "📚 Resource Moderation"
    ])

    # Tab 1: Official Announcement Publisher
    with tab_announcements:
        st.markdown("#### Create Official Announcement")
        st.caption("Official announcements are broadcast across all student feeds, marked with the verified 'Official Announcement' badge, and prioritized in the Smart Campus Feed.")

        with st.form(key="form_admin_announcement", clear_on_submit=True):
            ann_title = st.text_input("Announcement Headline", placeholder="e.g. End-Semester Examination Schedule Announced")
            ann_content = st.text_area("Official Notice Body", placeholder="Full announcement text, deadlines, faculty contacts...", height=140)
            ann_pin = st.checkbox("Pin to Top of Campus Feed", value=True)

            if st.form_submit_button("Publish Official Announcement 📢", type="primary"):
                v_t, e_t = validate_required_text(ann_title, "Headline", min_len=5, max_len=200)
                v_c, e_c = validate_required_text(ann_content, "Notice Body", min_len=10, max_len=5000)

                if not v_t:
                    st.error(e_t)
                elif not v_c:
                    st.error(e_c)
                else:
                    ok, msg = publish_official_announcement(admin_id, ann_title, ann_content, is_pinned=ann_pin)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


    # Tab 2: User Management
    with tab_users:
        st.markdown("#### Student & Faculty Directory")
        c_search, c_role = st.columns([2.5, 1])
        with c_search:
            u_search = st.text_input("Search Users", placeholder="Search by name, email, department...", label_visibility="collapsed")
        with c_role:
            u_role_filter = st.selectbox("Role Filter", options=["All", "Student", "Admin"], label_visibility="collapsed")

        users_list = get_all_users(search_query=u_search, role_filter=u_role_filter)

        if not users_list:
            render_empty_state("No users matching filter", "", "👥")
        else:
            # Display user table
            user_data = []
            for u in users_list:
                user_data.append({
                    "Name": u.get("full_name"),
                    "Email": u.get("email"),
                    "Department": u.get("department"),
                    "Year": u.get("year"),
                    "Role": u.get("role", "student").upper(),
                    "Joined": format_date_str(u.get("created_at")),
                    "ID": u.get("id")
                })
            df_users = pd.DataFrame(user_data)
            st.dataframe(df_users[["Name", "Email", "Department", "Year", "Role", "Joined"]], use_container_width=True)

            st.markdown("##### Change User Role")
            c_target, c_newrole, c_act = st.columns([2, 1, 1])
            with c_target:
                user_options = {f"{u['full_name']} ({u['email']})": u['id'] for u in users_list}
                selected_target_label = st.selectbox("Select User", options=list(user_options.keys()))
                target_id = user_options[selected_target_label] if selected_target_label else None
            with c_newrole:
                new_role_val = st.selectbox("Assign Role", options=["student", "admin"])
            with c_act:
                st.write("")
                st.write("")
                if st.button("Update Role", use_container_width=True):
                    if target_id:
                        ok_r, msg_r = update_user_role(target_id, new_role_val)
                        if ok_r:
                            st.success(msg_r)
                            st.rerun()
                        else:
                            st.error(msg_r)

    # Tab 3: Post Moderation
    with tab_posts:
        st.markdown("#### Campus Feed Moderation")
        p_search = st.text_input("Filter Posts for Review", placeholder="Search title or content...")
        all_posts = get_posts(search_query=p_search, limit=50)

        if not all_posts:
            render_empty_state("No posts found for moderation", "", "📝")
        else:
            for p in all_posts:
                p_id = p["id"]
                p_author = (p.get("author") or {}).get("full_name", "Unknown")
                p_cat = p.get("category", "")
                p_likes = p.get("likes_count", 0)

                col_p_info, col_p_del = st.columns([4, 1])
                with col_p_info:
                    with st.container(border=True):
                        st.markdown(f"**{clean_text(p.get('title', 'Untitled'))}**")
                        st.caption(f"Author: **{clean_text(p_author)}** &bull; Category: {clean_text(p_cat)} &bull; Likes: {p_likes}")
                with col_p_del:
                    if st.button("🗑️ Remove Post", key=f"admin_del_p_{p_id}", type="secondary"):
                        ok_dp, msg_dp = delete_post(p_id, admin_id, is_admin=True)
                        if ok_dp:
                            st.toast("Post removed by administrator.")
                            st.rerun()
                        else:
                            st.error(msg_dp)

    # Tab 4: Event Management & Attendee Roster
    with tab_events:
        st.markdown("#### Event Management & Attendance")

        with st.expander("➕ Create New Campus Event", expanded=False):
            with st.form(key="form_admin_create_event", clear_on_submit=True):
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

                if st.form_submit_button("Publish Event 🚀", type="primary"):
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
                                    created_by=admin_id,
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
        events_list = get_events()

        if not events_list:
            render_empty_state("No events to manage", "", "📅")
        else:
            for ev in events_list:
                ev_id = ev["id"]
                ev_title = ev.get("title")
                ev_date = format_date_str(ev.get("event_date"))
                ev_regs = ev.get("registration_count", 0)

                with st.expander(f"📅 {ev_title} ({ev_date}) — {ev_regs} Registrations"):
                    st.write(f"**Venue:** {ev.get('venue')} &bull; **Organizer:** {ev.get('organizer')}")
                    st.write(f"**Description:** {ev.get('description')}")

                    attendees = get_event_attendees(ev_id)
                    if attendees:
                        st.markdown("###### Registered Attendees:")
                        att_rows = []
                        for a in attendees:
                            u_info = a.get("user") or {}
                            att_rows.append({
                                "Name": u_info.get("full_name"),
                                "Email": u_info.get("email"),
                                "Department": u_info.get("department"),
                                "Year": u_info.get("year"),
                                "Registered At": format_date_str(a.get("registered_at"))
                            })
                        st.dataframe(pd.DataFrame(att_rows), use_container_width=True)
                    else:
                        st.caption("No attendees registered yet.")

                    if st.button(f"🗑️ Delete Event '{ev_title}'", key=f"admin_del_ev_{ev_id}", type="secondary"):
                        ok_de, msg_de = delete_event(ev_id, admin_id, is_admin=True)
                        if ok_de:
                            st.toast("Event deleted.")
                            st.rerun()
                        else:
                            st.error(msg_de)

    # Tab 5: Resource Hub Moderation
    with tab_resources:
        st.markdown("#### Academic Resource Moderation")
        res_list = get_resources()
        if not res_list:
            render_empty_state("No academic resources found", "", "📚")
        else:
            for r in res_list:
                r_id = r["id"]
                r_title = r.get("title")
                r_sub = r.get("subject")
                r_dept = r.get("department")
                r_uploader = (r.get("uploader") or {}).get("full_name", "Student")

                col_r_info, col_r_del = st.columns([4, 1])
                with col_r_info:
                    with st.container(border=True):
                        st.markdown(f"**{clean_text(r_title or 'Untitled')}**")
                        st.caption(f"Subject: {clean_text(r_sub)} &bull; Dept: {clean_text(r_dept)} &bull; Shared by: {clean_text(r_uploader)}")
                with col_r_del:
                    if st.button("🗑️ Remove", key=f"admin_del_res_{r_id}", type="secondary"):
                        ok_dr, msg_dr = delete_resource(r_id, admin_id, is_admin=True)
                        if ok_dr:
                            st.toast("Resource removed.")
                            st.rerun()
                        else:
                            st.error(msg_dr)


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_admin_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")

