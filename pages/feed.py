"""
Campus Konnect - Campus Feed & Smart Feed Page
Provides post publishing, multi-category browsing, keyword search,
and rule-based personalized recommendation ranking.
"""

from typing import List, Dict, Any
import streamlit as st
from services.auth import get_current_user, is_admin_user
from services.posts import create_post, get_posts
from services.recommendations import rank_posts_for_smart_feed
from components.ui_components import render_page_header, render_empty_state
from components.post_card import render_post_card
from utils.constants import POST_CATEGORIES, STUDENT_POST_CATEGORIES, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_FILE_SIZE_MB

from utils.validators import validate_required_text, validate_file_upload


def render_feed_page() -> None:
    """Render the central campus feed with Smart Feed ranking."""
    user = get_current_user()
    current_user_id = user.get("id") if user else None
    is_admin = is_admin_user()

    render_page_header(
        title="Campus Feed",
        subtitle="Discover real-time updates, academic notifications, and peer collaboration.",
        icon="📰"
    )

    # 1. Post Creation Expander
    with st.expander("✍️ Create a Campus Post", expanded=False):
        if not user:
            st.info("Please sign in to publish a post.")
        else:
            with st.form(key="form_create_post", clear_on_submit=True):
                post_title = st.text_input("Post Title", placeholder="Give your post a clear headline...")
                post_cat = st.selectbox("Category", options=STUDENT_POST_CATEGORIES)
                is_announcement = False
                is_pinned = False



                post_content = st.text_area(
                    "Content",
                    placeholder="Share announcements, opportunities, project ideas, or questions...",
                    height=120
                )

                uploaded_img = st.file_uploader(
                    "Attach Image (Optional)",
                    type=ALLOWED_IMAGE_EXTENSIONS,
                    help=f"Supported: {', '.join(ALLOWED_IMAGE_EXTENSIONS)} up to {MAX_IMAGE_FILE_SIZE_MB}MB"
                )

                submit_btn = st.form_submit_button("Publish Post 🚀", type="primary", use_container_width=True)

                if submit_btn:
                    valid_t, err_t = validate_required_text(post_title, "Title", min_len=3, max_len=200)
                    valid_c, err_c = validate_required_text(post_content, "Content", min_len=5, max_len=5000)

                    if not valid_t:
                        st.error(err_t)
                    elif not valid_c:
                        st.error(err_c)
                    else:
                        img_bytes = None
                        img_name = None
                        img_type = "image/jpeg"
                        img_valid = True

                        if uploaded_img:
                            img_valid, img_err = validate_file_upload(
                                uploaded_img.name,
                                uploaded_img.size,
                                ALLOWED_IMAGE_EXTENSIONS,
                                MAX_IMAGE_FILE_SIZE_MB
                            )
                            if not img_valid:
                                st.error(img_err)
                            else:
                                img_bytes = uploaded_img.getvalue()
                                img_name = uploaded_img.name
                                img_type = uploaded_img.type or "image/jpeg"

                        if img_valid:
                            with st.spinner("Publishing post to campus feed..."):
                                ok, msg, _ = create_post(
                                    author_id=current_user_id,
                                    title=post_title,
                                    content=post_content,
                                    category=post_cat,
                                    image_bytes=img_bytes,
                                    image_name=img_name,
                                    mime_type=img_type,
                                    is_announcement=is_announcement,
                                    is_pinned=is_pinned
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

    st.write("")

    # 2. Feed Search, Filters & Smart Sorting Controls
    col_search, col_filter, col_sort = st.columns([2, 1.2, 1.4])

    with col_search:
        search_query = st.text_input("Search Posts", placeholder="Search by title, keywords...", label_visibility="collapsed")

    with col_filter:
        cat_options = ["All Categories"] + POST_CATEGORIES
        selected_category = st.selectbox("Category Filter", options=cat_options, label_visibility="collapsed")

    with col_sort:
        sort_options = [
            "⚡ Smart Campus Feed",
            "🕒 Latest First",
            "❤️ Most Liked",
            "💬 Most Discussed"
        ]
        sort_by = st.selectbox("Sort Order", options=sort_options, label_visibility="collapsed")

    # Smart Feed Educational Banner
    if sort_by == "⚡ Smart Campus Feed":
        st.info(
            "💡 **Smart Campus Feed**: Your feed prioritizes campus content based on your academic profile, department, and interests.",
            icon="⚡"
        )

    # 3. Fetch Posts
    cat_param = selected_category if selected_category != "All Categories" else None
    posts = get_posts(
        category=cat_param,
        search_query=search_query,
        current_user_id=current_user_id,
        limit=50
    )

    # Apply Sorting
    if sort_by == "⚡ Smart Campus Feed":
        posts = rank_posts_for_smart_feed(posts, user)
        show_score = True
    elif sort_by == "❤️ Most Liked":
        posts = sorted(posts, key=lambda p: (p.get("is_pinned", False), p.get("likes_count", 0)), reverse=True)
        show_score = False
    elif sort_by == "💬 Most Discussed":
        posts = sorted(posts, key=lambda p: (p.get("is_pinned", False), p.get("comments_count", 0)), reverse=True)
        show_score = False
    else:  # Latest First
        show_score = False

    st.write("")

    # 4. Render Post Stream
    if not posts:
        render_empty_state(
            title="No posts found",
            subtitle="Try clearing your search filters or be the first to publish a new post!",
            icon="📝"
        )
    else:
        for idx, p in enumerate(posts):
            render_post_card(p, current_user_id=current_user_id, show_smart_score=show_score, context_id=f"feed_{idx}")


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_feed_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")

