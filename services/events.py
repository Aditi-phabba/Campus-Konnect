"""
Campus Konnect - Events & Registration Service
Handles event creation, discovery, filtering, registration, and attendance tracking.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import date
from services.database import get_supabase_client, upload_file_to_storage
from utils.constants import BUCKET_EVENT_IMAGES


def create_event(
    title: str,
    description: str,
    category: str,
    event_date: str,
    start_time: str,
    end_time: str,
    venue: str,
    organizer: str,
    created_by: str,
    registration_link: str = "",
    image_bytes: Optional[bytes] = None,
    image_name: Optional[str] = None,
    mime_type: str = "image/jpeg"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Create a new campus event."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available.", None

    # Enforce role-based permission: Only administrators can create events
    try:
        prof_res = client.table("profiles").select("role").eq("id", created_by).execute()
        user_role = prof_res.data[0].get("role") if prof_res.data else "student"
    except Exception:
        user_role = "student"

    if user_role != "admin":
        return False, "Unauthorized: Only campus administrators can create campus events.", None

    image_url = ""
    if image_bytes and image_name:
        import uuid
        ext = image_name.rsplit(".", 1)[-1].lower() if "." in image_name else "jpg"
        dest_path = f"events/{created_by}_{uuid.uuid4().hex[:8]}.{ext}"
        ok, res_url = upload_file_to_storage(BUCKET_EVENT_IMAGES, dest_path, image_bytes, mime_type)
        if ok:
            image_url = res_url

    payload = {
        "title": title.strip(),
        "description": description.strip(),
        "category": category,
        "event_date": str(event_date),
        "start_time": str(start_time),
        "end_time": str(end_time),
        "venue": venue.strip(),
        "organizer": organizer.strip(),
        "registration_link": registration_link.strip(),
        "image_url": image_url,
        "created_by": created_by
    }

    try:
        res = client.table("events").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return True, "Event created successfully!", res.data[0]
        return False, "Failed to create event.", None
    except Exception as e:
        return False, f"Event creation error: {e}", None


def update_event(
    event_id: str,
    user_id: str,
    updates: Dict[str, Any],
    is_admin: bool = False
) -> Tuple[bool, str]:
    """Update event information (Admin only)."""
    if not is_admin:
        return False, "Unauthorized: Only administrators can modify events."

    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("events").update(updates).eq("id", event_id)
        res = query.execute()
        if res.data:
            return True, "Event updated successfully."
        return False, "Event not found or unable to update."
    except Exception as e:
        return False, f"Error updating event: {e}"


def delete_event(event_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, str]:
    """Delete an event (Admin only)."""
    if not is_admin:
        return False, "Unauthorized: Only administrators can delete events."

    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("events").delete().eq("id", event_id)
        res = query.execute()
        if res.data:
            return True, "Event deleted successfully."
        return False, "Event not found or unable to delete."
    except Exception as e:
        return False, f"Error deleting event: {e}"



def get_events(
    category: Optional[str] = None,
    search_query: Optional[str] = None,
    current_user_id: Optional[str] = None,
    only_registered_by_user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve events enriched with attendee counts and user registration status."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        query = client.table("events").select(
            "*, creator:profiles!events_created_by_fkey(full_name, avatar_url, department)"
        )

        if category and category != "All Categories":
            query = query.eq("category", category)

        if search_query and search_query.strip():
            query = query.or_(f"title.ilike.%{search_query.strip()}%,description.ilike.%{search_query.strip()}%,venue.ilike.%{search_query.strip()}%")

        query = query.order("event_date", desc=False).order("start_time", desc=False)
        res = query.execute()
        events = res.data or []

        if not events:
            return []

        # If filtering by registered events
        if only_registered_by_user_id:
            reg_res = client.table("event_registrations").select("event_id").eq("user_id", only_registered_by_user_id).eq("status", "registered").execute()
            reg_ids = {r["event_id"] for r in (reg_res.data or [])}
            events = [e for e in events if e["id"] in reg_ids]
            if not events:
                return []

        event_ids = [e["id"] for e in events]

        # Fetch registrations count
        regs_res = client.table("event_registrations").select("event_id, user_id, status").in_("event_id", event_ids).eq("status", "registered").execute()
        regs_data = regs_res.data or []

        reg_counts: Dict[str, int] = {}
        user_reg_set = set()

        for r in regs_data:
            eid = r["event_id"]
            reg_counts[eid] = reg_counts.get(eid, 0) + 1
            if current_user_id and r["user_id"] == current_user_id:
                user_reg_set.add(eid)

        today_iso = date.today().isoformat()
        for e in events:
            eid = e["id"]
            e["registration_count"] = reg_counts.get(eid, 0)
            e["is_registered"] = eid in user_reg_set
            edate = str(e.get("event_date", ""))
            if edate > today_iso:
                e["timeline"] = "upcoming"
            elif edate == today_iso:
                e["timeline"] = "today"
            else:
                e["timeline"] = "past"

        return events

    except Exception as e:
        print(f"Error fetching events: {e}")
        return []


def register_for_event(event_id: str, user_id: str) -> Tuple[bool, str]:
    """Register student for an event."""
    client = get_supabase_client()
    if not client or not user_id:
        return False, "Authentication required."

    try:
        # Check existing registration
        existing = client.table("event_registrations").select("id, status").eq("event_id", event_id).eq("user_id", user_id).execute()
        if existing.data and len(existing.data) > 0:
            reg = existing.data[0]
            if reg.get("status") == "registered":
                return False, "You are already registered for this event."
            else:
                client.table("event_registrations").update({"status": "registered"}).eq("id", reg["id"]).execute()
                return True, "Event registration renewed successfully!"

        client.table("event_registrations").insert({
            "event_id": event_id,
            "user_id": user_id,
            "status": "registered"
        }).execute()
        return True, "Successfully registered for this event!"
    except Exception as e:
        return False, f"Registration failed: {e}"


def cancel_event_registration(event_id: str, user_id: str) -> Tuple[bool, str]:
    """Cancel event registration."""
    client = get_supabase_client()
    if not client or not user_id:
        return False, "Authentication required."

    try:
        client.table("event_registrations").delete().eq("event_id", event_id).eq("user_id", user_id).execute()
        return True, "Your event registration has been cancelled."
    except Exception as e:
        return False, f"Error cancelling registration: {e}"


def get_event_attendees(event_id: str) -> List[Dict[str, Any]]:
    """Fetch registered attendees for an event (Admin / Organizer feature)."""
    client = get_supabase_client()
    if not client or not event_id:
        return []

    try:
        res = client.table("event_registrations").select(
            "registered_at, status, user:profiles!event_registrations_user_id_fkey(id, full_name, email, department, year)"
        ).eq("event_id", event_id).eq("status", "registered").execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching attendees: {e}")
        return []
