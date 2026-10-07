"""
Campus Konnect - Academic Resource Hub Service
Manages academic study material, lecture notes, lab manuals, question papers,
and integrates with Supabase Storage.
"""

from typing import Optional, Dict, Any, List, Tuple
from services.database import get_supabase_client, upload_file_to_storage, delete_file_from_storage
from utils.constants import BUCKET_RESOURCES


def upload_resource(
    title: str,
    description: str,
    department: str,
    semester: int,
    subject: str,
    resource_type: str,
    file_name: str,
    file_bytes: bytes,
    mime_type: str,
    uploaded_by: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Upload academic file to Supabase Storage and register metadata in database."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available.", None

    import uuid
    safe_name = file_name.replace(" ", "_")
    storage_path = f"{department.replace(' ', '_')}/sem_{semester}/{uuid.uuid4().hex[:8]}_{safe_name}"

    ok, file_url = upload_file_to_storage(BUCKET_RESOURCES, storage_path, file_bytes, mime_type)
    if not ok:
        return False, f"File upload failed: {file_url}", None

    payload = {
        "title": title.strip(),
        "description": description.strip(),
        "department": department,
        "semester": int(semester),
        "subject": subject.strip(),
        "resource_type": resource_type,
        "file_url": file_url,
        "file_name": file_name,
        "file_size_bytes": len(file_bytes),
        "uploaded_by": uploaded_by
    }

    try:
        res = client.table("resources").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return True, "Academic resource uploaded successfully!", res.data[0]
        return False, "Could not save resource details.", None
    except Exception as e:
        return False, f"Database error: {e}", None


def get_resources(
    department: Optional[str] = None,
    semester: Optional[int] = None,
    subject: Optional[str] = None,
    resource_type: Optional[str] = None,
    search_query: Optional[str] = None,
    uploaded_by: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Query academic resources with filtering and search."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        query = client.table("resources").select(
            "*, uploader:profiles!resources_uploaded_by_fkey(full_name, avatar_url, department, role)"
        )

        if uploaded_by:
            query = query.eq("uploaded_by", uploaded_by)

        if department and department != "All Departments":
            query = query.eq("department", department)

        if semester and semester != 0:
            query = query.eq("semester", semester)

        if resource_type and resource_type != "All Types":
            query = query.eq("resource_type", resource_type)

        if subject and subject.strip() and subject != "All Subjects":
            query = query.ilike("subject", f"%{subject.strip()}%")

        if search_query and search_query.strip():
            query = query.or_(f"title.ilike.%{search_query.strip()}%,description.ilike.%{search_query.strip()}%,subject.ilike.%{search_query.strip()}%")

        query = query.order("created_at", desc=True)
        res = query.execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching resources: {e}")
        return []


def delete_resource(resource_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, str]:
    """Delete a resource file and database record."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("resources").delete().eq("id", resource_id)
        if not is_admin:
            query = query.eq("uploaded_by", user_id)
        res = query.execute()
        if res.data:
            return True, "Resource deleted successfully."
        return False, "Permission denied or resource not found."
    except Exception as e:
        return False, f"Error deleting resource: {e}"
