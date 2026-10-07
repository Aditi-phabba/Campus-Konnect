"""
Campus Konnect - Discussion Forum Service
Manages student forum threads, discussions, replies, search, and moderation.
"""

from typing import Optional, Dict, Any, List, Tuple
from services.database import get_supabase_client


def create_discussion(
    title: str,
    description: str,
    category: str,
    author_id: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Create a new discussion thread."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available.", None

    payload = {
        "title": title.strip(),
        "description": description.strip(),
        "category": category,
        "author_id": author_id
    }

    try:
        res = client.table("discussions").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return True, "Discussion thread created successfully!", res.data[0]
        return False, "Could not create discussion thread.", None
    except Exception as e:
        return False, f"Error creating discussion: {e}", None


def get_discussions(
    category: Optional[str] = None,
    search_query: Optional[str] = None,
    author_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Retrieve discussions with author information and reply counts."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        query = client.table("discussions").select(
            "*, author:profiles!discussions_author_id_fkey(full_name, avatar_url, department, year, role)"
        )

        if author_id:
            query = query.eq("author_id", author_id)

        if category and category != "All Categories":
            query = query.eq("category", category)

        if search_query and search_query.strip():
            query = query.or_(f"title.ilike.%{search_query.strip()}%,description.ilike.%{search_query.strip()}%")

        query = query.order("created_at", desc=True).limit(limit)
        res = query.execute()
        discussions = res.data or []

        if not discussions:
            return []

        disc_ids = [d["id"] for d in discussions]

        # Fetch reply counts
        comments_res = client.table("discussion_comments").select("discussion_id").in_("discussion_id", disc_ids).execute()
        cdata = comments_res.data or []
        counts: Dict[str, int] = {}
        for c in cdata:
            did = c["discussion_id"]
            counts[did] = counts.get(did, 0) + 1

        for d in discussions:
            d["replies_count"] = counts.get(d["id"], 0)

        return discussions
    except Exception as e:
        print(f"Error fetching discussions: {e}")
        return []


def delete_discussion(discussion_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, str]:
    """Delete a discussion thread."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("discussions").delete().eq("id", discussion_id)
        if not is_admin:
            query = query.eq("author_id", user_id)
        res = query.execute()
        if res.data:
            return True, "Discussion deleted."
        return False, "Permission denied."
    except Exception as e:
        return False, f"Error deleting discussion: {e}"


def get_discussion_comments(discussion_id: str) -> List[Dict[str, Any]]:
    """Fetch replies for a discussion thread."""
    client = get_supabase_client()
    if not client or not discussion_id:
        return []

    try:
        res = client.table("discussion_comments").select(
            "*, author:profiles!discussion_comments_author_id_fkey(full_name, avatar_url, department, year, role)"
        ).eq("discussion_id", discussion_id).order("created_at", desc=False).execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching discussion replies: {e}")
        return []


def add_discussion_comment(
    discussion_id: str,
    author_id: str,
    content: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Post a reply to a discussion."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available.", None

    if not content or not content.strip():
        return False, "Reply content cannot be empty.", None

    payload = {
        "discussion_id": discussion_id,
        "author_id": author_id,
        "content": content.strip()
    }

    try:
        res = client.table("discussion_comments").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return True, "Reply posted successfully.", res.data[0]
        return False, "Failed to submit reply.", None
    except Exception as e:
        return False, f"Error submitting reply: {e}", None


def delete_discussion_comment(comment_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, str]:
    """Delete a discussion reply."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("discussion_comments").delete().eq("id", comment_id)
        if not is_admin:
            query = query.eq("author_id", user_id)
        res = query.execute()
        if res.data:
            return True, "Reply removed."
        return False, "Permission denied."
    except Exception as e:
        return False, f"Error deleting reply: {e}"
