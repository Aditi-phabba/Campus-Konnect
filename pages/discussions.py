"""
Campus Konnect - Discussion Forum Page
Enables campus-wide student discussions across academics, placements,
projects, clubs, and general campus questions.
"""

import streamlit as st
from services.auth import get_current_user
from services.discussions import create_discussion, get_discussions
from components.ui_components import render_page_header, render_empty_state
from components.discussion_card import render_discussion_card
from utils.constants import DISCUSSION_CATEGORIES
from utils.validators import validate_required_text


def render_discussions_page() -> None:
    """Render the Discussion Forum interface."""
    user = get_current_user()
    current_user_id = user.get("id") if user else None

    render_page_header(
        title="Discussion Forum",
        subtitle="Ask peer questions, discuss placement interview experiences, and find project teammates.",
        icon="💬"
    )

    # 1. Start Discussion Expander
    with st.expander("💭 Start a New Campus Discussion", expanded=False):
        if not user:
            st.info("Please sign in to start a discussion thread.")
        else:
            with st.form(key="form_new_discussion", clear_on_submit=True):
                disc_title = st.text_input("Discussion Topic / Question", placeholder="e.g. Any advice for Google Summer of Code / campus placements?")
                disc_cat = st.selectbox("Topic Category", options=DISCUSSION_CATEGORIES)
                disc_desc = st.text_area("Detailed Context", placeholder="Provide background or details so peers can give specific advice...", height=120)

                submit_d = st.form_submit_button("Post Discussion Thread 🚀", type="primary", use_container_width=True)

                if submit_d:
                    valid_t, err_t = validate_required_text(disc_title, "Topic", min_len=5, max_len=200)
                    valid_d, err_d = validate_required_text(disc_desc, "Context", min_len=10, max_len=4000)

                    if not valid_t:
                        st.error(err_t)
                    elif not valid_d:
                        st.error(err_d)
                    else:
                        with st.spinner("Posting discussion..."):
                            ok, msg, _ = create_discussion(
                                title=disc_title,
                                description=disc_desc,
                                category=disc_cat,
                                author_id=current_user_id
                            )
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    st.write("")

    # 2. Search & Filter
    col_search, col_filter = st.columns([2.5, 1.5])
    with col_search:
        search_query = st.text_input("Search Discussions", placeholder="Search topics, questions...", label_visibility="collapsed")
    with col_filter:
        cat_options = ["All Categories"] + DISCUSSION_CATEGORIES
        selected_category = st.selectbox("Category", options=cat_options, label_visibility="collapsed")

    # 3. Retrieve Discussions
    cat_param = selected_category if selected_category != "All Categories" else None
    discussions = get_discussions(
        category=cat_param,
        search_query=search_query
    )

    st.write("")

    # 4. Render Thread Stream
    if not discussions:
        render_empty_state(
            title="No discussions found",
            subtitle="Start the first conversation in this category to help fellow students!",
            icon="💬"
        )
    else:
        for idx, d in enumerate(discussions):
            render_discussion_card(d, current_user_id=current_user_id, context_id=f"disc_{idx}")


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_discussions_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")

