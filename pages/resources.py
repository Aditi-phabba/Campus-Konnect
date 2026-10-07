"""
Campus Konnect - Academic Resource Hub Page
Enables students to share and discover lecture notes, previous exam papers,
lab records, and study references with full Supabase Storage integration.
"""

import streamlit as st
from services.auth import get_current_user
from services.resources import upload_resource, get_resources
from services.recommendations import rank_resources_for_user
from components.ui_components import render_page_header, render_empty_state
from components.resource_card import render_resource_card
from utils.constants import (
    DEPARTMENTS,
    RESOURCE_TYPES,
    SEMESTERS,
    ALLOWED_RESOURCE_EXTENSIONS,
    MAX_RESOURCE_FILE_SIZE_MB
)
from utils.validators import validate_required_text, validate_file_upload


def render_resources_page() -> None:
    """Render the Academic Resource Hub interface."""
    user = get_current_user()
    current_user_id = user.get("id") if user else None

    render_page_header(
        title="Academic Resource Hub",
        subtitle="Centralized repository of student lecture notes, question papers, and syllabus materials.",
        icon="📚"
    )

    # 1. Upload Material Form
    with st.expander("📤 Upload Academic Study Material", expanded=False):
        if not user:
            st.info("Please sign in to upload course materials.")
        else:
            with st.form(key="form_upload_resource", clear_on_submit=True):
                res_title = st.text_input("Resource Title", placeholder="e.g. Unit 3 - Operating Systems Memory Management Notes")

                col_dept, col_sem = st.columns([2, 1])
                with col_dept:
                    # Pre-select student's own department if possible
                    user_dept = user.get("department")
                    default_idx = DEPARTMENTS.index(user_dept) if user_dept in DEPARTMENTS else 0
                    res_dept = st.selectbox("Department", options=DEPARTMENTS, index=default_idx)
                with col_sem:
                    res_sem = st.selectbox("Semester", options=SEMESTERS)

                col_sub, col_type = st.columns([2, 1])
                with col_sub:
                    res_sub = st.text_input("Subject / Course Name", placeholder="e.g. Computer Networks")
                with col_type:
                    res_type = st.selectbox("Resource Type", options=RESOURCE_TYPES)

                res_desc = st.text_area("Description / Topic Summary (Optional)", placeholder="Summarize what topics or questions are covered in this document...")

                uploaded_file = st.file_uploader(
                    f"Choose Academic File ({', '.join(ALLOWED_RESOURCE_EXTENSIONS)})",
                    type=ALLOWED_RESOURCE_EXTENSIONS,
                    help=f"Maximum file size: {MAX_RESOURCE_FILE_SIZE_MB}MB"
                )

                submit_res = st.form_submit_button("Upload to Resource Hub 🚀", type="primary", use_container_width=True)

                if submit_res:
                    valid_t, err_t = validate_required_text(res_title, "Resource Title", min_len=3, max_len=150)
                    valid_s, err_s = validate_required_text(res_sub, "Subject", min_len=2, max_len=100)

                    if not valid_t:
                        st.error(err_t)
                    elif not valid_s:
                        st.error(err_s)
                    elif not uploaded_file:
                        st.error("Please select a file to upload.")
                    else:
                        file_valid, file_err = validate_file_upload(
                            uploaded_file.name,
                            uploaded_file.size,
                            ALLOWED_RESOURCE_EXTENSIONS,
                            MAX_RESOURCE_FILE_SIZE_MB
                        )
                        if not file_valid:
                            st.error(file_err)
                        else:
                            with st.spinner("Uploading document to secure cloud storage..."):
                                ok, msg, _ = upload_resource(
                                    title=res_title,
                                    description=res_desc,
                                    department=res_dept,
                                    semester=res_sem,
                                    subject=res_sub,
                                    resource_type=res_type,
                                    file_name=uploaded_file.name,
                                    file_bytes=uploaded_file.getvalue(),
                                    mime_type=uploaded_file.type or "application/octet-stream",
                                    uploaded_by=current_user_id
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

    st.write("")

    # 2. Filters & Search Controls
    col_search, col_fdept, col_fsem, col_ftype = st.columns([1.5, 1.2, 0.8, 1])

    with col_search:
        search_query = st.text_input("Search Resources", placeholder="Search by title, subject...", label_visibility="collapsed")
    with col_fdept:
        dept_options = ["All Departments"] + DEPARTMENTS
        f_dept = st.selectbox("Filter Department", options=dept_options, label_visibility="collapsed")
    with col_fsem:
        sem_options = ["All Sems"] + [f"Sem {s}" for s in SEMESTERS]
        f_sem_str = st.selectbox("Semester", options=sem_options, label_visibility="collapsed")
        f_sem = int(f_sem_str.replace("Sem ", "")) if f_sem_str != "All Sems" else None
    with col_ftype:
        type_options = ["All Types"] + RESOURCE_TYPES
        f_type = st.selectbox("Type", options=type_options, label_visibility="collapsed")

    # 3. Retrieve Resources
    raw_resources = get_resources(
        department=f_dept if f_dept != "All Departments" else None,
        semester=f_sem,
        resource_type=f_type if f_type != "All Types" else None,
        search_query=search_query
    )

    # Apply curriculum smart matching
    ranked_resources = rank_resources_for_user(raw_resources, user)

    st.write("")

    # 4. Display Results
    if not ranked_resources:
        render_empty_state(
            title="No academic resources found",
            subtitle="Be the first to upload lecture notes or previous papers for this subject!",
            icon="📚"
        )
    else:
        st.caption(f"Showing **{len(ranked_resources)}** academic materials")
        for idx, res in enumerate(ranked_resources):
            render_resource_card(res, current_user_id=current_user_id, context_id=f"hub_{idx}")


if __name__ == "__main__":
    from services.auth import is_authenticated
    from components.sidebar import render_sidebar
    from components.ui_components import inject_custom_css

    inject_custom_css()
    if is_authenticated():
        render_sidebar()
        render_resources_page()
    else:
        st.warning("Please sign in from the main portal (app.py) first.")

