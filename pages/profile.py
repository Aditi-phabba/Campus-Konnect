"""
Campus Konnect - Student Profile Page
Enables students to view and update their academic profile, upload an avatar,
and manage their activity (My Posts, Saved Posts, Registrations, Resources).
All cards are rendered with native Streamlit components and unique context keys.
"""

import streamlit as st
from services.auth import get_current_user, refresh_user_profile
from services.users import update_user_profile, upload_avatar, get_user_activity_counts
from services.posts import get_posts
from services.events import get_events
from services.resources import get_resources
from components.ui_components import render_page_header, render_metric_card, render_empty_state
from components.post_card import render_post_card
from components.event_card import render_event_card
from components.resource_card import render_resource_card
from utils.constants import DEPARTMENTS, YEARS, INTEREST_OPTIONS, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_FILE_SIZE_MB
from utils.validators import validate_required_text, validate_file_upload
from utils.helpers import format_date_str, format_member_since, clean_text, format_student_year


def render_profile_page() -> None:
    """Render the student profile and activity center."""
    user = get_current_user()
    if not user:
        st.warning("Please sign in to view your profile.")
        return

    user_id = user["id"]
    email = clean_text(user.get("email", ""))
    full_name = clean_text(user.get("full_name", "Student"))
    dept = clean_text(user.get("department", "Computer Science"))
    year = user.get("year", 1)
    interests = user.get("interests", []) or []
    bio = clean_text(user.get("bio", ""))
    avatar_url = user.get("avatar_url", "")
    role = str(user.get("role", "student")).strip().lower()
    created_at = format_member_since(user.get("created_at"))

    render_page_header(
        title="Student Profile",
        subtitle="Manage your personal information, interests, and review your campus footprint.",
        icon="👤"
    )

    # 1. Profile Overview Card & Quick Edit
    col_prof_view, col_prof_edit = st.columns([1.2, 1.8], gap="large")

    with col_prof_view:
        with st.container(border=True):
            if avatar_url:
                c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
                with c_img2:
                    st.image(avatar_url, width=100)
            else:
                st.markdown(f"### 👤 {full_name}")

            st.markdown(f"**{full_name}**")
            st.caption(email)

            role_badge_color = "orange" if role == "admin" else "blue"
            st.markdown(f":{role_badge_color}-badge[{role.upper()}]")

            year_text = format_student_year(year)
            st.markdown(f"**Department:** {dept}  \n**Academic Year:** {year_text}")

            if bio:
                st.info(f'"{bio}"')

            st.caption(f"Member since {created_at}")

        # Avatar Upload Form
        with st.expander("📷 Change Profile Picture"):
            avatar_file = st.file_uploader("Upload New Avatar", type=ALLOWED_IMAGE_EXTENSIONS, key="avatar_uploader")
            if avatar_file and st.button("Save New Avatar", key="btn_save_avatar", use_container_width=True):
                v_ok, v_err = validate_file_upload(avatar_file.name, avatar_file.size, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_FILE_SIZE_MB)
                if not v_ok:
                    st.error(v_err)
                else:
                    with st.spinner("Uploading avatar to cloud storage..."):
                        up_ok, up_msg = upload_avatar(
                            user_id,
                            avatar_file.name,
                            avatar_file.getvalue(),
                            avatar_file.type or "image/jpeg"
                        )
                        if up_ok:
                            refresh_user_profile()
                            st.success("Avatar updated!")
                            st.rerun()
                        else:
                            st.error(up_msg)

    with col_prof_edit:
        st.markdown("#### ✏️ Update Profile Information")
        with st.form(key="form_edit_profile"):
            new_name = st.text_input("Full Name", value=full_name)

            col_d, col_y = st.columns([2, 1])
            with col_d:
                dept_idx = DEPARTMENTS.index(dept) if dept in DEPARTMENTS else 0
                new_dept = st.selectbox("Department", options=DEPARTMENTS, index=dept_idx)
            with col_y:
                year_idx = YEARS.index(year) if year in YEARS else 0
                new_year = st.selectbox("Academic Year", options=YEARS, index=year_idx)

            new_interests = st.multiselect(
                "Interests & Specializations",
                options=INTEREST_OPTIONS,
                default=[i for i in interests if i in INTEREST_OPTIONS]
            )

            new_bio = st.text_area("Bio / About Me", value=bio, placeholder="Tell campus peers about your technical passions and goals...")

            save_profile_btn = st.form_submit_button("Save Profile Changes 💾", type="primary", use_container_width=True)

            if save_profile_btn:
                valid_n, err_n = validate_required_text(new_name, "Full Name", min_len=2, max_len=100)
                if not valid_n:
                    st.error(err_n)
                else:
                    with st.spinner("Saving profile updates..."):
                        ok_up, msg_up = update_user_profile(user_id, {
                            "full_name": new_name,
                            "department": new_dept,
                            "year": new_year,
                            "interests": new_interests,
                            "bio": new_bio
                        })
                        if ok_up:
                            refresh_user_profile()
                            st.success("Profile updated successfully!")
                            st.rerun()
                        else:
                            st.error(msg_up)

    st.write("")

    # 2. Activity Metrics
    stats = get_user_activity_counts(user_id)
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        render_metric_card("My Posts", stats["posts_count"], "📝")
    with s2:
        render_metric_card("Comments", stats["comments_count"], "💬")
    with s3:
        render_metric_card("Saved Posts", stats["saved_posts_count"], "🔖")
    with s4:
        render_metric_card("Registered Events", stats["registered_events_count"], "🎟️")
    with s5:
        render_metric_card("Uploaded Resources", stats["resources_count"], "📚")

    st.write("")

    # 3. Activity Detail Tabs with unique context IDs for cards
    tab_posts, tab_saved, tab_events, tab_resources = st.tabs([
        f"📝 My Posts ({stats['posts_count']})",
        f"🔖 Saved Posts ({stats['saved_posts_count']})",
        f"🎟️ My Events ({stats['registered_events_count']})",
        f"📚 My Resources ({stats['resources_count']})"
    ])

    with tab_posts:
        my_posts = get_posts(only_user_id=user_id, current_user_id=user_id)
        if not my_posts:
            render_empty_state("No posts published yet", "Share your thoughts or news in the Campus Feed!", "📝")
        else:
            for idx, p in enumerate(my_posts):
                render_post_card(p, current_user_id=user_id, context_id=f"prof_my_{idx}")

    with tab_saved:
        saved_posts = get_posts(only_saved_by_user_id=user_id, current_user_id=user_id)
        if not saved_posts:
            render_empty_state("No saved posts", "Click the 🔖 Save button on any post in the feed to save it for later.", "🔖")
        else:
            for idx, p in enumerate(saved_posts):
                render_post_card(p, current_user_id=user_id, context_id=f"prof_saved_{idx}")

    with tab_events:
        my_events = get_events(current_user_id=user_id, only_registered_by_user_id=user_id)
        if not my_events:
            render_empty_state("No registered events", "Browse upcoming workshops and hackathons in the Events section.", "🎟️")
        else:
            for idx, ev in enumerate(my_events):
                render_event_card(ev, current_user_id=user_id, context_id=f"prof_ev_{idx}")

    with tab_resources:
        my_resources = get_resources(uploaded_by=user_id)
        if not my_resources:
            render_empty_state("No resources uploaded yet", "Contribute lecture notes or past papers in the Resource Hub.", "📚")
        else:
            for idx, r in enumerate(my_resources):
                render_resource_card(r, current_user_id=user_id, context_id=f"prof_res_{idx}")


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_profile_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")
