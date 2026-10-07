"""
Campus Konnect - Admin Service
Administrative management for users, roles, announcements, content moderation,
and system-wide metrics.
"""

from typing import Dict, Any, List, Tuple
from services.database import get_supabase_client
from utils.helpers import clean_text


def get_admin_dashboard_metrics() -> Dict[str, int]:
    """Calculate platform-wide totals for admin overview metrics."""
    client = get_supabase_client()
    metrics = {
        "total_users": 0,
        "total_posts": 0,
        "total_events": 0,
        "total_resources": 0,
        "total_discussions": 0,
        "total_registrations": 0,
    }
    if not client:
        return metrics

    try:
        u = client.table("profiles").select("id", count="exact").execute()
        metrics["total_users"] = u.count or len(u.data or [])

        p = client.table("posts").select("id", count="exact").execute()
        metrics["total_posts"] = p.count or len(p.data or [])

        e = client.table("events").select("id", count="exact").execute()
        metrics["total_events"] = e.count or len(e.data or [])

        r = client.table("resources").select("id", count="exact").execute()
        metrics["total_resources"] = r.count or len(r.data or [])

        d = client.table("discussions").select("id", count="exact").execute()
        metrics["total_discussions"] = d.count or len(d.data or [])

        reg = client.table("event_registrations").select("id", count="exact").eq("status", "registered").execute()
        metrics["total_registrations"] = reg.count or len(reg.data or [])
    except Exception as exc:
        print(f"Error fetching admin metrics: {exc}")

    return metrics


def get_all_users(search_query: str = "", role_filter: str = "All") -> List[Dict[str, Any]]:
    """Retrieve all student profiles for administrative monitoring."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        query = client.table("profiles").select("*").order("created_at", desc=True)
        if role_filter != "All":
            query = query.eq("role", role_filter.lower())
        if search_query.strip():
            query = query.or_(f"full_name.ilike.%{search_query.strip()}%,email.ilike.%{search_query.strip()}%,department.ilike.%{search_query.strip()}%")

        res = query.execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []


def update_user_role(target_user_id: str, new_role: str) -> Tuple[bool, str]:
    """Change a user's role (student <-> admin)."""
    if new_role not in ["student", "admin"]:
        return False, "Invalid role specified."

    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        res = client.table("profiles").update({"role": new_role}).eq("id", target_user_id).execute()
        if res.data:
            return True, f"User role updated to '{new_role}'."
        return False, "Unable to update user role."
    except Exception as e:
        return False, f"Error updating role: {e}"


def publish_official_announcement(
    admin_id: str,
    title: str,
    content: str,
    is_pinned: bool = True
) -> Tuple[bool, str]:
    """Publish a verified campus-wide official announcement."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    # Verify that the author is an administrator
    try:
        prof_res = client.table("profiles").select("role").eq("id", admin_id).execute()
        user_role = prof_res.data[0].get("role") if prof_res.data else "student"
    except Exception:
        user_role = "student"

    if user_role != "admin":
        return False, "You are not authorized to create official announcements."

    title_clean = clean_text(title)
    content_clean = clean_text(content)

    payload = {
        "author_id": admin_id,
        "title": title_clean,
        "content": content_clean,
        "category": "Announcement",
        "is_announcement": True,
        "is_pinned": is_pinned
    }


    try:
        res = client.table("posts").insert(payload).execute()
        if res.data:
            return True, "Official campus announcement published successfully!"
        return False, "Could not publish announcement."
    except Exception as e:
        return False, f"Error publishing announcement: {e}"
