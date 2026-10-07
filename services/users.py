"""
Campus Konnect - User Profile Service
Handles profile retrieval, profile updates, avatar uploads, and user activity statistics.
"""

from typing import Optional, Dict, Any, List, Tuple
from services.database import get_supabase_client, upload_file_to_storage
from utils.constants import BUCKET_PROFILE_IMAGES


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full profile details for a given user ID."""
    client = get_supabase_client()
    if not client or not user_id:
        return None

    try:
        res = client.table("profiles").select("*").eq("id", user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception as e:
        print(f"Error fetching profile for {user_id}: {e}")
    return None


def update_user_profile(user_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
    """Update profile information (e.g. name, department, year, interests, bio, avatar)."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        # Filter allowed update fields
        allowed_keys = ["full_name", "department", "year", "interests", "bio", "avatar_url"]
        payload = {k: v for k, v in updates.items() if k in allowed_keys}
        if not payload:
            return False, "No valid fields provided for update."

        res = client.table("profiles").update(payload).eq("id", user_id).execute()
        if res.data:
            return True, "Profile updated successfully."
        return False, "Unable to update profile. Please try again."
    except Exception as e:
        return False, f"Failed to update profile: {e}"


def upload_avatar(user_id: str, file_name: str, file_bytes: bytes, mime_type: str) -> Tuple[bool, str]:
    """Upload user avatar to Supabase Storage and update profile avatar_url."""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "jpg"
    path = f"{user_id}/avatar_{user_id}.{ext}"

    success, url_or_err = upload_file_to_storage(BUCKET_PROFILE_IMAGES, path, file_bytes, mime_type)
    if not success:
        return False, url_or_err

    # Update profile avatar_url
    update_ok, msg = update_user_profile(user_id, {"avatar_url": url_or_err})
    if update_ok:
        return True, url_or_err
    return False, msg


def get_user_activity_counts(user_id: str) -> Dict[str, int]:
    """Fetch count statistics of user activity across Campus Konnect."""
    client = get_supabase_client()
    stats = {
        "posts_count": 0,
        "comments_count": 0,
        "saved_posts_count": 0,
        "registered_events_count": 0,
        "resources_count": 0,
    }
    if not client or not user_id:
        return stats

    try:
        p_res = client.table("posts").select("id", count="exact").eq("author_id", user_id).execute()
        stats["posts_count"] = p_res.count or len(p_res.data or [])
    except Exception:
        pass

    try:
        c_res = client.table("comments").select("id", count="exact").eq("author_id", user_id).execute()
        stats["comments_count"] = c_res.count or len(c_res.data or [])
    except Exception:
        pass

    try:
        s_res = client.table("saved_posts").select("id", count="exact").eq("user_id", user_id).execute()
        stats["saved_posts_count"] = s_res.count or len(s_res.data or [])
    except Exception:
        pass

    try:
        e_res = client.table("event_registrations").select("id", count="exact").eq("user_id", user_id).eq("status", "registered").execute()
        stats["registered_events_count"] = e_res.count or len(e_res.data or [])
    except Exception:
        pass

    try:
        r_res = client.table("resources").select("id", count="exact").eq("uploaded_by", user_id).execute()
        stats["resources_count"] = r_res.count or len(r_res.data or [])
    except Exception:
        pass

    return stats
