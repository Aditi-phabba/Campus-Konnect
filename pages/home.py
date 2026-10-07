"""
Campus Konnect - Home / Dashboard Page
Provides a personalized dashboard overview with quick statistics,
official announcements, upcoming events, and Smart Feed highlights.
"""

import streamlit as st
from services.auth import get_current_user
from services.posts import get_posts
from services.events import get_events
from services.resources import get_resources
from services.discussions import get_discussions
from services.recommendations import rank_posts_for_smart_feed
from components.ui_components import render_page_header, render_metric_card, render_empty_state
from components.post_card import render_post_card
from components.event_card import render_event_card
from utils.helpers import clean_text


def render_home_page() -> None:
    """Render the main student dashboard."""
    user = get_current_user()
    if not user:
        st.warning("Please log in to view the dashboard.")
        return

    full_name = user.get("full_name", "Student")
    user_id = user.get("id")

    # Header
    render_page_header(
        title=f"Welcome back, {full_name}!",
        subtitle="Here is what is happening across your campus community today.",
        icon="👋"
    )

    # Fetch latest data
    posts = get_posts(current_user_id=user_id, limit=20)
    events = get_events(current_user_id=user_id)
    resources = get_resources()
    discussions = get_discussions(limit=10)

    upcoming_events = [e for e in events if e.get("timeline") in ["upcoming", "today"]]
    my_regs = [e for e in events if e.get("is_registered")]

    # Quick Stats Metric Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Upcoming Events", len(upcoming_events), "📅")
    with c2:
        render_metric_card("Study Resources", len(resources), "📚")
    with c3:
        render_metric_card("Active Discussions", len(discussions), "💬")
    with c4:
        render_metric_card("My Registered Events", len(my_regs), "🎟️")

    st.write("")

    # Two column layout: Left (Smart Highlights & Announcements), Right (Upcoming Events & Discussions)
    col_main, col_side = st.columns([1.8, 1.2], gap="large")

    with col_main:
        # Smart Recommendations Spotlight
        st.markdown("### ⚡ Recommended for You")
        st.caption("Content prioritized based on your academic profile, department, and interests.")

        ranked_posts = rank_posts_for_smart_feed(posts, user)
        if ranked_posts:
            # Show top 2 ranked posts
            for idx, p in enumerate(ranked_posts[:2]):
                render_post_card(p, current_user_id=user_id, show_smart_score=True, context_id=f"home_rec_{idx}")
        else:
            render_empty_state(
                "No recommendations yet",
                "New posts and announcements will appear here personalized for you.",
                "🌱"
            )

        # Official Campus Announcements
        st.markdown("### 📢 Official Announcements")
        announcements = [p for p in posts if p.get("is_announcement") or p.get("category") == "Announcement"]
        if announcements:
            for idx, ann in enumerate(announcements[:2]):
                render_post_card(ann, current_user_id=user_id, show_smart_score=False, context_id=f"home_ann_{idx}")
        else:
            render_empty_state("No official announcements today", "Check back soon for university notices.", "📢")

    with col_side:
        # Upcoming Events Spotlight
        st.markdown("### 📅 Upcoming Events")
        if upcoming_events:
            for idx, ev in enumerate(upcoming_events[:2]):
                render_event_card(ev, current_user_id=user_id, context_id=f"home_ev_{idx}")
            if len(upcoming_events) > 2:
                if st.button("View All Events →", key="btn_more_events", use_container_width=True):
                    st.session_state["active_page"] = "events"
                    st.rerun()
        else:
            render_empty_state("No upcoming events", "Stay tuned for new workshops and hackathons.", "🗓️")

        st.write("")

        # Recent Discussions Snippet
        st.markdown("### 💬 Active Conversations")
        if discussions:
            for d in discussions[:3]:
                d_cat = clean_text(d.get("category", "General"))
                d_reps = d.get("replies_count", 0)
                d_title = clean_text(d.get("title", ""))
                with st.container(border=True):
                    st.markdown(f"**{d_title}**")
                    st.caption(f"🏷️ {d_cat} &bull; 💬 {d_reps} replies")
            if st.button("Join Discussions →", key="btn_more_disc", use_container_width=True):
                st.session_state["active_page"] = "discussions"
                st.rerun()
        else:
            render_empty_state("No discussions yet", "Start the conversation in the Forum.", "💬")


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_home_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")

