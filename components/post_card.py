"""
Campus Konnect - Post Card Component
Renders a clean social post card with author metadata, native badges,
safe text rendering, likes, comments, bookmarking, and moderation.
All interactive widgets use unique, context-aware keys to prevent StreamlitDuplicateElementKey.
"""

from typing import Dict, Any, Optional
import streamlit as st
from utils.helpers import (
    format_relative_time,
    clean_text,
    sanitize_post_content,
    format_student_year,
    get_badge_props
)
from services.posts import (
    toggle_like,
    toggle_save,
    delete_post,
    get_post_comments,
    add_post_comment,
    delete_post_comment
)
from services.auth import is_admin_user


def render_post_card(
    post: Dict[str, Any],
    current_user_id: Optional[str] = None,
    show_smart_score: bool = False,
    context_id: str = "feed"
) -> None:
    """Render a post card cleanly using native Streamlit containers and components."""
    post_id = post["id"]
    author = post.get("author") or {}
    author_name = clean_text(author.get("full_name", "Campus Member"))
    author_dept = clean_text(author.get("department", "Student"))
    author_role_raw = str(author.get("role") or "student").strip().lower()
    author_role = "Admin" if author_role_raw == "admin" else "Student"
    author_year = author.get("year", 1)
    author_id = post.get("author_id", "")

    category = clean_text(post.get("category", "General"))
    created_at = post.get("created_at")
    image_url = post.get("image_url", "")
    is_pinned = bool(post.get("is_pinned", False))
    is_announcement = bool(post.get("is_announcement", False)) or (category.lower() == "announcement")

    # Sanitize title and content so no HTML tags are ever shown
    title = clean_text(post.get("title", ""))
    content = sanitize_post_content(post.get("content", ""), is_announcement=is_announcement)

    likes_count = post.get("likes_count", 0)
    comments_count = post.get("comments_count", 0)
    has_liked = post.get("has_liked", False)
    has_saved = post.get("has_saved", False)
    raw_smart_score = post.get("_smart_score", None)
    smart_score = 0.0
    if isinstance(raw_smart_score, (int, float)):
        smart_score = float(raw_smart_score)
    elif isinstance(raw_smart_score, str):
        try:
            smart_score = float(raw_smart_score)
        except ValueError:
            smart_score = 0.0

    is_author = bool(current_user_id and current_user_id == author_id)
    is_admin = is_admin_user()
    time_str = format_relative_time(created_at)

    if author_role == "Admin":
        role_year_text = "Admin"
    else:
        role_year_text = f"Student • {format_student_year(author_year)}"

    with st.container(border=True):
        # 1. Author Metadata Header
        st.markdown(f"**👤 {author_name}**")
        st.caption(f"{author_dept}  \n{role_year_text} &bull; {time_str}")

        # 2. Badges Row (Rendered cleanly with native Streamlit badge markdown)
        badges = []
        if is_announcement:
            badges.append(("📢 Official Announcement", "orange"))
        else:
            cat_label, cat_color = get_badge_props(category)
            badges.append((cat_label, cat_color))

        if is_pinned:
            badges.append(("📌 Pinned", "blue"))

        if show_smart_score and smart_score > 0:
            score_disp = int(smart_score) if smart_score.is_integer() else smart_score
            badges.append((f"⚡ Smart Score +{score_disp}", "violet"))

        if badges:
            badge_md = " ".join([f":{b_color}-badge[{b_label}]" for b_label, b_color in badges])
            st.markdown(badge_md)

        # 3. Post Title
        if title:
            st.markdown(f"### {title}")

        # 4. Post Content (Safely rendered as text without raw HTML)
        if content:
            st.markdown(content)

        # 5. Image Attachment if present
        if image_url:
            st.image(image_url, use_container_width=True)

        st.markdown("---")

        # 6. Action Bar: Like, Comments, Save, and Delete with context-aware keys
        col_like, col_comm, col_save, col_del = st.columns([1.2, 1.2, 1.3, 1.8])

        # Like Button
        with col_like:
            like_icon = "❤️" if has_liked else "🤍"
            like_label = f"{like_icon} {likes_count}"
            if st.button(like_label, key=f"btn_like_{post_id}_{context_id}", help="Like or unlike this post"):
                if current_user_id:
                    ok, is_liked_now, msg = toggle_like(post_id, current_user_id)
                    if ok:
                        st.rerun()
                else:
                    st.warning("Please sign in to like posts.")

        # Comments Toggle
        comm_state_key = f"show_comments_{post_id}_{context_id}"
        with col_comm:
            comments_label = f"💬 {comments_count}"
            if st.button(comments_label, key=f"btn_comm_toggle_{post_id}_{context_id}", help="View or add comments"):
                st.session_state[comm_state_key] = not st.session_state.get(comm_state_key, False)
                st.rerun()

        # Save Button
        with col_save:
            save_icon = "🔖 Saved" if has_saved else "🔖 Save"
            if st.button(save_icon, key=f"btn_save_{post_id}_{context_id}", help="Save to your profile"):
                if current_user_id:
                    ok, is_saved_now, msg = toggle_save(post_id, current_user_id)
                    if ok:
                        st.toast(msg)
                        st.rerun()
                else:
                    st.warning("Please sign in to save posts.")

        # Delete Action (Author or Admin)
        with col_del:
            if is_author or is_admin:
                del_label = "🗑️ Delete (Admin)" if is_admin and not is_author else "🗑️ Delete"
                if st.button(del_label, key=f"btn_del_post_{post_id}_{context_id}", type="secondary"):
                    ok, msg = delete_post(post_id, current_user_id or "", is_admin=is_admin)
                    if ok:
                        st.toast("Post removed.")
                        st.rerun()
                    else:
                        st.error(msg)

        # 7. Comments Section (Expanded when toggled)
        if st.session_state.get(comm_state_key, False):
            st.markdown("---")
            st.caption(f"**Comments ({comments_count})**")

            comments = get_post_comments(post_id)
            if not comments:
                st.caption("No comments yet. Be the first to share your thoughts!")
            else:
                for c in comments:
                    c_id = c["id"]
                    c_author = c.get("author") or {}
                    c_name = clean_text(c_author.get("full_name", "Student"))
                    c_dept = clean_text(c_author.get("department", ""))
                    c_time = format_relative_time(c.get("created_at"))
                    c_content = clean_text(c.get("content", ""))
                    c_author_id = c.get("author_id", "")

                    with st.container(border=True):
                        c_col1, c_col2 = st.columns([5, 1])
                        with c_col1:
                            st.caption(f"**{c_name}** ({c_dept}) &bull; {c_time}")
                            st.markdown(c_content)
                        with c_col2:
                            if current_user_id and (current_user_id == c_author_id or is_admin):
                                if st.button("✕", key=f"del_c_{c_id}_{context_id}", help="Delete comment"):
                                    delete_post_comment(c_id, current_user_id, is_admin=is_admin)
                                    st.rerun()

            # Add comment form
            if current_user_id:
                with st.form(key=f"form_comm_{post_id}_{context_id}", clear_on_submit=True):
                    new_comm = st.text_input(
                        "Add a comment",
                        key=f"input_comm_{post_id}_{context_id}",
                        placeholder="Write a constructive reply...",
                        label_visibility="collapsed"
                    )
                    submit_comm = st.form_submit_button("Reply", use_container_width=False)
                    if submit_comm:
                        clean_comm = clean_text(new_comm)
                        if clean_comm:
                            ok, msg, _ = add_post_comment(post_id, current_user_id, clean_comm)
                            if ok:
                                st.toast("Comment added.")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Comment cannot be empty.")
