"""
Campus Konnect - Posts & Feed Service
Handles posts creation, retrieval, updates, deletions, likes, saves, and comments.
"""

from typing import Optional, Dict, Any, List, Tuple
from services.database import get_supabase_client, upload_file_to_storage
from utils.constants import BUCKET_POST_MEDIA
from utils.helpers import clean_text


def create_post(
    author_id: str,
    title: str,
    content: str,
    category: str,
    image_bytes: Optional[bytes] = None,
    image_name: Optional[str] = None,
    mime_type: str = "image/jpeg",
    is_announcement: bool = False,
    is_pinned: bool = False
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Create a new post in the campus feed."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available.", None

    category_clean = (category or "").strip()
    is_announcement_flag = bool(is_announcement) or (category_clean.lower() == "announcement")

    # Enforce role-based permission: Only administrators can publish announcements or pin posts
    if is_announcement_flag or bool(is_pinned):
        try:
            prof_res = client.table("profiles").select("role").eq("id", author_id).execute()
            user_role = prof_res.data[0].get("role") if prof_res.data else "student"
        except Exception:
            user_role = "student"

        if user_role != "admin":
            return False, "You are not authorized to create official announcements.", None

    image_url = ""
    if image_bytes and image_name:
        import uuid
        ext = image_name.rsplit(".", 1)[-1].lower() if "." in image_name else "jpg"
        dest_path = f"posts/{author_id}_{uuid.uuid4().hex[:8]}.{ext}"
        ok, res_url = upload_file_to_storage(BUCKET_POST_MEDIA, dest_path, image_bytes, mime_type)
        if ok:
            image_url = res_url

    # Sanitize title and content before storing so no raw HTML enters the database
    title_clean = clean_text(title)
    content_clean = clean_text(content)

    payload = {
        "author_id": author_id,
        "title": title_clean,
        "content": content_clean,
        "category": "Announcement" if is_announcement_flag else category_clean,
        "image_url": image_url,
        "is_announcement": is_announcement_flag,
        "is_pinned": bool(is_pinned)
    }

    try:
        res = client.table("posts").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return True, "Post published successfully!", res.data[0]
        return False, "Failed to publish post.", None
    except Exception as e:
        return False, f"Post creation failed: {e}", None


def get_posts(
    category: Optional[str] = None,
    search_query: Optional[str] = None,
    current_user_id: Optional[str] = None,
    only_user_id: Optional[str] = None,
    only_saved_by_user_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch posts with author profile details, like count, comment count,
    and user-specific like/save interaction states.
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        # Build query
        query = client.table("posts").select(
            "*, author:profiles!posts_author_id_fkey(id, full_name, avatar_url, department, year, role)"
        )

        if only_user_id:
            query = query.eq("author_id", only_user_id)

        if category and category != "All Categories":
            query = query.eq("category", category)

        if search_query and search_query.strip():
            # Filter by title or content
            query = query.or_(f"title.ilike.%{search_query.strip()}%,content.ilike.%{search_query.strip()}%")

        # Order by pinned first, then created_at desc
        query = query.order("is_pinned", desc=True).order("created_at", desc=True).limit(limit)
        res = query.execute()
        posts = res.data or []

        if not posts:
            return []

        # If filtering by saved posts
        if only_saved_by_user_id:
            saved_res = client.table("saved_posts").select("post_id").eq("user_id", only_saved_by_user_id).execute()
            saved_ids = {item["post_id"] for item in (saved_res.data or [])}
            posts = [p for p in posts if p["id"] in saved_ids]
            if not posts:
                return []

        post_ids = [p["id"] for p in posts]

        # Fetch likes count & user likes
        likes_res = client.table("likes").select("post_id, user_id").in_("post_id", post_ids).execute()
        likes_data = likes_res.data or []
        likes_map: Dict[str, int] = {}
        user_liked_set = set()
        for l in likes_data:
            pid = l["post_id"]
            likes_map[pid] = likes_map.get(pid, 0) + 1
            if current_user_id and l["user_id"] == current_user_id:
                user_liked_set.add(pid)

        # Fetch comments count
        comments_res = client.table("comments").select("post_id").in_("post_id", post_ids).execute()
        comments_data = comments_res.data or []
        comments_map: Dict[str, int] = {}
        for c in comments_data:
            pid = c["post_id"]
            comments_map[pid] = comments_map.get(pid, 0) + 1

        # Fetch saved set for current user
        user_saved_set = set()
        if current_user_id:
            user_saved_res = client.table("saved_posts").select("post_id").eq("user_id", current_user_id).in_("post_id", post_ids).execute()
            for s in (user_saved_res.data or []):
                user_saved_set.add(s["post_id"])

        # Attach metadata to each post
        for p in posts:
            pid = p["id"]
            p["likes_count"] = likes_map.get(pid, 0)
            p["comments_count"] = comments_map.get(pid, 0)
            p["has_liked"] = pid in user_liked_set
            p["has_saved"] = pid in user_saved_set

        return posts

    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []


def update_post(
    post_id: str,
    user_id: str,
    title: str,
    content: str,
    category: str,
    is_admin: bool = False
) -> Tuple[bool, str]:
    """Update a post if user is the author or an admin."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    category_clean = (category or "").strip()
    if category_clean.lower() == "announcement" and not is_admin:
        return False, "You are not authorized to create official announcements."

    title_clean = clean_text(title)
    content_clean = clean_text(content)

    try:
        query = client.table("posts").update({
            "title": title_clean,
            "content": content_clean,
            "category": category_clean
        }).eq("id", post_id)

        if not is_admin:
            query = query.eq("author_id", user_id)

        res = query.execute()
        if res.data:
            return True, "Post updated successfully."
        return False, "You do not have permission to edit this post."
    except Exception as e:
        return False, f"Error updating post: {e}"


def delete_post(post_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, str]:
    """Delete a post if user is the author or an admin."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("posts").delete().eq("id", post_id)
        if not is_admin:
            query = query.eq("author_id", user_id)

        res = query.execute()
        if res.data:
            return True, "Post deleted successfully."
        return False, "You do not have permission to delete this post."
    except Exception as e:
        return False, f"Error deleting post: {e}"


def toggle_like(post_id: str, user_id: str) -> Tuple[bool, bool, str]:
    """
    Toggle like on a post. Returns (success, is_liked_now, message).
    """
    client = get_supabase_client()
    if not client or not user_id:
        return False, False, "Authentication required."

    try:
        # Check if already liked
        existing = client.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        if existing.data and len(existing.data) > 0:
            # Unlike
            client.table("likes").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            return True, False, "Like removed"
        else:
            # Like
            client.table("likes").insert({"post_id": post_id, "user_id": user_id}).execute()
            return True, True, "Post liked!"
    except Exception as e:
        return False, False, f"Could not update like: {e}"


def toggle_save(post_id: str, user_id: str) -> Tuple[bool, bool, str]:
    """
    Toggle save post for current user. Returns (success, is_saved_now, message).
    """
    client = get_supabase_client()
    if not client or not user_id:
        return False, False, "Authentication required."

    try:
        existing = client.table("saved_posts").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        if existing.data and len(existing.data) > 0:
            # Unsave
            client.table("saved_posts").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            return True, False, "Post removed from saved list"
        else:
            # Save
            client.table("saved_posts").insert({"post_id": post_id, "user_id": user_id}).execute()
            return True, True, "Post saved to your profile!"
    except Exception as e:
        return False, False, f"Could not update save: {e}"


# -----------------------------------------------------------------------------
# Comments Functions
# -----------------------------------------------------------------------------

def get_post_comments(post_id: str) -> List[Dict[str, Any]]:
    """Retrieve all comments for a post ordered chronologically."""
    client = get_supabase_client()
    if not client or not post_id:
        return []

    try:
        res = client.table("comments").select(
            "*, author:profiles!comments_author_id_fkey(id, full_name, avatar_url, department, role)"
        ).eq("post_id", post_id).order("created_at", desc=False).execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching comments for post {post_id}: {e}")
        return []


def add_post_comment(post_id: str, author_id: str, content: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Add a new comment to a post."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available.", None

    content_clean = clean_text(content)
    if not content_clean:
        return False, "Comment cannot be empty.", None

    try:
        payload = {
            "post_id": post_id,
            "author_id": author_id,
            "content": content_clean
        }
        res = client.table("comments").insert(payload).execute()
        if res.data and len(res.data) > 0:
            return True, "Comment posted successfully.", res.data[0]
        return False, "Could not save comment.", None
    except Exception as e:
        return False, f"Error adding comment: {e}", None


def delete_post_comment(comment_id: str, user_id: str, is_admin: bool = False) -> Tuple[bool, str]:
    """Delete a comment if user is author or an admin."""
    client = get_supabase_client()
    if not client:
        return False, "Database client is not available."

    try:
        query = client.table("comments").delete().eq("id", comment_id)
        if not is_admin:
            query = query.eq("author_id", user_id)
        res = query.execute()
        if res.data:
            return True, "Comment deleted."
        return False, "Permission denied."
    except Exception as e:
        return False, f"Error deleting comment: {e}"
