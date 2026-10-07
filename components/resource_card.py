"""
Campus Konnect - Resource Card Component
Renders cards for downloadable lecture notes, previous question papers,
and lab study materials using native Streamlit containers and components.
All interactive widgets use unique, context-aware keys to prevent StreamlitDuplicateElementKey.
"""

from typing import Dict, Any, Optional
import streamlit as st
from utils.helpers import format_file_size, format_date_str, clean_text
from services.resources import delete_resource
from services.auth import is_admin_user


def render_resource_card(
    resource: Dict[str, Any],
    current_user_id: Optional[str] = None,
    context_id: str = "resources"
) -> None:
    """Render an academic resource item with download link and metadata."""
    res_id = resource["id"]
    title = clean_text(resource.get("title", ""))
    description = clean_text(resource.get("description", ""))
    department = clean_text(resource.get("department", ""))
    semester = resource.get("semester", 1)
    subject = clean_text(resource.get("subject", ""))
    resource_type = clean_text(resource.get("resource_type", "Notes"))
    file_url = resource.get("file_url", "")
    file_name = clean_text(resource.get("file_name", "download"))
    file_size_bytes = resource.get("file_size_bytes", 0)
    uploaded_by = resource.get("uploaded_by", "")
    created_at = format_date_str(resource.get("created_at"))

    uploader = resource.get("uploader") or {}
    uploader_name = clean_text(uploader.get("full_name", "Student"))

    raw_smart_score = resource.get("_smart_score", None)
    smart_score = 0.0
    if isinstance(raw_smart_score, (int, float)):
        smart_score = float(raw_smart_score)
    elif isinstance(raw_smart_score, str):
        try:
            smart_score = float(raw_smart_score)
        except ValueError:
            smart_score = 0.0

    is_owner = bool(current_user_id and current_user_id == uploaded_by)
    is_admin = is_admin_user()

    # File extension icon
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "file"
    icons = {
        "pdf": "📄",
        "doc": "📝",
        "docx": "📝",
        "ppt": "📊",
        "pptx": "📊",
        "jpg": "🖼️",
        "png": "🖼️",
    }
    icon = icons.get(ext, "📁")
    size_str = format_file_size(file_size_bytes)

    with st.container(border=True):
        # 1. Badges & Date Header
        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            badges = [
                (f"{icon} {resource_type}", "blue"),
                (f"Sem {semester}", "violet"),
            ]
            if smart_score > 0:
                score_disp = int(smart_score) if smart_score.is_integer() else smart_score
                badges.append((f"⚡ Curriculum Match +{score_disp}", "green"))

            badge_md = " ".join([f":{b_color}-badge[{b_label}]" for b_label, b_color in badges])
            st.markdown(badge_md)

        with col_b2:
            st.caption(f"📅 Uploaded {created_at}")

        # 2. Resource Title
        st.markdown(f"### {title}")

        # 3. Subject & Department
        st.markdown(f"**Subject:** {subject} &bull; **Department:** {department}")

        # 4. Description if present
        if description:
            st.markdown(description)

        # 5. Metadata Footer
        st.caption(f"👤 Shared by **{uploader_name}** &bull; 📦 {file_name} ({size_str})")

        st.markdown("---")

        # 6. Action Controls
        col_dl, col_del = st.columns([3, 1])
        with col_dl:
            if file_url:
                st.link_button(f"📥 Download / View File ({ext.upper()})", file_url, key=f"dl_btn_{res_id}_{context_id}", use_container_width=True)
            else:
                st.caption("No file link available")

        with col_del:
            if is_owner or is_admin:
                del_label = "🗑️ Delete (Admin)" if is_admin and not is_owner else "🗑️ Delete"
                if st.button(del_label, key=f"del_res_{res_id}_{context_id}", type="secondary"):
                    ok, msg = delete_resource(res_id, current_user_id or "", is_admin=is_admin)
                    if ok:
                        st.toast("Resource deleted.")
                        st.rerun()
                    else:
                        st.error(msg)
