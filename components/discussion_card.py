"""
Campus Konnect - Discussion Card Component
Renders discussion forum threads with reply counts, replies list, reply composer,
and thread moderation using native Streamlit containers and components.
All interactive widgets use unique, context-aware keys to prevent StreamlitDuplicateElementKey.
"""

from typing import Dict, Any, Optional
import streamlit as st
from utils.helpers import format_relative_time, clean_text, get_badge_props
from services.discussions import (
    get_discussion_comments,
    add_discussion_comment,
    delete_discussion,
    delete_discussion_comment
)
from services.auth import is_admin_user


def render_discussion_card(
    discussion: Dict[str, Any],
    current_user_id: Optional[str] = None,
    context_id: str = "discussions"
) -> None:
    """Render an interactive discussion forum card cleanly."""
    disc_id = discussion["id"]
    title = clean_text(discussion.get("title", ""))
    description = clean_text(discussion.get("description", ""))
    category = clean_text(discussion.get("category", "General"))
    created_at = discussion.get("created_at")
    replies_count = discussion.get("replies_count", 0)
    author_id = discussion.get("author_id", "")

    author = discussion.get("author") or {}
    author_name = clean_text(author.get("full_name", "Student"))
    author_dept = clean_text(author.get("department", "Campus Member"))

    is_author = bool(current_user_id and current_user_id == author_id)
    is_admin = is_admin_user()
    time_str = format_relative_time(created_at)

    with st.container(border=True):
        # 1. Category Badge & Started Date Header
        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            cat_label, cat_color = get_badge_props(category)
            st.markdown(f":{cat_color}-badge[{cat_label}]")
        with col_b2:
            st.caption(f"🕒 Started {time_str}")

        # 2. Topic Title
        st.markdown(f"### {title}")

        # 3. Topic Description / Details
        if description:
            st.markdown(description)

        # 4. Author & Responses Count
        st.caption(f"👤 **{author_name}** &bull; {author_dept} &bull; 💬 **{replies_count} Responses**")

        st.markdown("---")

        # 5. Controls Row
        col_expand, col_del = st.columns([4, 1.2])
        with col_expand:
            show_replies = st.checkbox(f"💬 View & Join Discussion ({replies_count})", key=f"chk_disc_{disc_id}_{context_id}", value=False)

        with col_del:
            if is_author or is_admin:
                del_label = "🗑️ Delete (Admin)" if is_admin and not is_author else "🗑️ Delete"
                if st.button(del_label, key=f"del_disc_{disc_id}_{context_id}", type="secondary"):
                    ok, msg = delete_discussion(disc_id, current_user_id or "", is_admin=is_admin)
                    if ok:
                        st.toast("Discussion deleted.")
                        st.rerun()
                    else:
                        st.error(msg)

        # 6. Replies Section
        if show_replies:
            st.markdown("---")
            st.caption(f"**Discussion Replies ({replies_count})**")

            replies = get_discussion_comments(disc_id)
            if not replies:
                st.caption("No replies yet. Share your thoughts below!")
            else:
                for r in replies:
                    r_id = r["id"]
                    r_author = r.get("author") or {}
                    r_name = clean_text(r_author.get("full_name", "Student"))
                    r_dept = clean_text(r_author.get("department", ""))
                    r_time = format_relative_time(r.get("created_at"))
                    r_content = clean_text(r.get("content", ""))
                    r_author_id = r.get("author_id", "")

                    with st.container(border=True):
                        r_col1, r_col2 = st.columns([5, 1])
                        with r_col1:
                            st.caption(f"**{r_name}** ({r_dept}) &bull; {r_time}")
                            st.markdown(r_content)
                        with r_col2:
                            if current_user_id and (current_user_id == r_author_id or is_admin):
                                if st.button("✕", key=f"del_dr_{r_id}_{context_id}", help="Delete reply"):
                                    delete_discussion_comment(r_id, current_user_id, is_admin=is_admin)
                                    st.rerun()

            if current_user_id:
                with st.form(key=f"form_disc_rep_{disc_id}_{context_id}", clear_on_submit=True):
                    rep_text = st.text_area(
                        "Your response",
                        key=f"text_disc_rep_{disc_id}_{context_id}",
                        placeholder="Share your perspective or answer...",
                        label_visibility="collapsed"
                    )
                    if st.form_submit_button("Post Response"):
                        clean_rep = clean_text(rep_text)
                        if clean_rep:
                            ok, msg, _ = add_discussion_comment(disc_id, current_user_id, clean_rep)
                            if ok:
                                st.toast("Response posted.")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Response cannot be empty.")
