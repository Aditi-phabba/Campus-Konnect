"""
Campus Konnect - Helper Functions
Formatting, date helpers, badges, and utility calculations.
"""

import re
from datetime import datetime, timezone, date, time
from typing import Any, Optional, Tuple


import html


def clean_text(text: Any) -> str:
    """
    Sanitize and strip any accidental or malicious HTML tags and entities so
    user-generated content displays safely and purely as readable text.
    Preserves math inequalities like x < 5 and y > 10.
    """
    if text is None:
        return ""
    s = html.unescape(str(text))
    # 1. Strip script and style blocks entirely along with their inner contents
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.IGNORECASE | re.DOTALL)
    # 2. Convert common HTML block elements / linebreaks to newlines
    s = re.sub(r"<(?:br\s*/?|/p|/div|/li|/h[1-6])>", "\n", s, flags=re.IGNORECASE)
    # 3. Strip all HTML tags while preserving inequalities like x < 5 and y > 10
    s = re.sub(r"<(?:[a-zA-Z/][^>]*|!--.*?--)>", "", s)
    # 4. Remove unclosed tags at the edges
    s = re.sub(r"</?[a-zA-Z0-9_-]+(?:\s+[^>]*)?>?", "", s)
    # 5. Normalize multiple newlines
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def sanitize_post_content(content_text: Any, is_announcement: bool = False) -> str:
    """
    Sanitize post content text and strip any accidental UI badge markup
    that may have been prepended to test data.
    """
    cleaned = clean_text(content_text)
    if is_announcement:
        for prefix in [
            "📢 Official Announcement",
            "📢 Announcement",
            "Official Announcement",
            "[Official Announcement]",
            "Announcement:"
        ]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].lstrip(" :\n-")
    return cleaned.strip()


def format_student_year(year: Any) -> str:
    """Format student academic year to friendly ordinal ('1st Year', '2nd Year', etc.)."""
    try:
        y = int(year)
        if y == 1:
            return "1st Year"
        elif y == 2:
            return "2nd Year"
        elif y == 3:
            return "3rd Year"
        elif y >= 4:
            return f"{y}th Year"
    except Exception:
        pass
    return f"Year {year}"


def get_badge_props(category: str) -> Tuple[str, str]:
    """Return (label, streamlit_badge_color) for native Streamlit badge rendering."""
    cat_clean = clean_text(category).strip()
    mapping = {
        "Announcement": ("📢 Official Announcement", "orange"),
        "Academic": ("📚 Academic", "blue"),
        "Opportunity": ("🚀 Opportunity", "green"),
        "Club": ("🎯 Club", "violet"),
        "Placement": ("💼 Placement", "green"),
        "General": ("💬 General", "gray"),
        "Workshop": ("🛠️ Workshop", "blue"),
        "Seminar": ("🎤 Seminar", "violet"),
        "Hackathon": ("💻 Hackathon", "red"),
        "Cultural": ("🎭 Cultural", "violet"),
        "Sports": ("🏆 Sports", "green"),
        "Other": ("📌 Other", "gray"),
    }
    return mapping.get(cat_clean, (f"📌 {cat_clean}", "blue"))



def parse_datetime(dt_val: Any) -> Optional[datetime]:
    """Parse various ISO formats into a timezone-aware datetime."""
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val
    try:
        # Replace trailing Z with UTC offset
        s = str(dt_val).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def format_relative_time(dt_val: Any) -> str:
    """Return friendly relative time (e.g., 'Just now', '5m ago', '2h ago', 'Yesterday', 'Oct 12')."""
    dt = parse_datetime(dt_val)
    if not dt:
        return "Recently"

    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "Just now"
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        mins = seconds // 60
        return f"{mins}m ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h ago"
    if seconds < 172800:
        return "Yesterday"
    if seconds < 604800:
        days = seconds // 86400
        return f"{days}d ago"

    return dt.strftime("%b %d, %Y")


def format_date_str(dt_val: Any) -> str:
    """Format date to human readable 'Oct 12, 2026'."""
    if isinstance(dt_val, (date, datetime)):
        return dt_val.strftime("%b %d, %Y")
    dt = parse_datetime(dt_val)
    if dt:
        return dt.strftime("%b %d, %Y")
    return str(dt_val or "N/A")


def format_member_since(dt_val: Any) -> str:
    """Format join date cleanly to 'Oct 2026' without raw HTML or seconds."""
    if not dt_val:
        return "Oct 2026"
    dt = parse_datetime(dt_val)
    if dt:
        return dt.strftime("%b %Y")
    if isinstance(dt_val, (date, datetime)):
        return dt_val.strftime("%b %Y")
    clean_s = clean_text(dt_val)
    return clean_s if clean_s else "Oct 2026"



def format_time_str(time_val: Any) -> str:
    """Format time object or string to '02:30 PM'."""
    if isinstance(time_val, time):
        return time_val.strftime("%I:%M %p")
    try:
        parts = str(time_val).split(":")
        h, m = int(parts[0]), int(parts[1])
        t = time(h, m)
        return t.strftime("%I:%M %p")
    except Exception:
        return str(time_val or "")


def format_file_size(size_bytes: Optional[int]) -> str:
    """Convert bytes to readable string (e.g. 2.4 MB)."""
    if not size_bytes or size_bytes <= 0:
        return "Unknown size"
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    idx = 0
    while size >= 1024.0 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    return f"{size:.1f} {units[idx]}"


def truncate_text(text: str, max_chars: int = 150) -> str:
    """Truncate text safely with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def get_category_color(category: str) -> dict:
    """Return styling tokens for categories."""
    palette = {
        "Announcement": {"bg": "#EFF6FF", "text": "#1E40AF", "border": "#BFDBFE", "icon": "📢"},
        "Academic": {"bg": "#F0FDF4", "text": "#166534", "border": "#BBF7D0", "icon": "📚"},
        "Event": {"bg": "#FAF5FF", "text": "#6B21A8", "border": "#E9D5FF", "icon": "📅"},
        "Opportunity": {"bg": "#FFFBEB", "text": "#92400E", "border": "#FDE68A", "icon": "🚀"},
        "Club": {"bg": "#FDF2F8", "text": "#9D174D", "border": "#FBCFE8", "icon": "🎯"},
        "Placement": {"bg": "#ECFDF5", "text": "#065F46", "border": "#A7F3D0", "icon": "💼"},
        "General": {"bg": "#F1F5F9", "text": "#334155", "border": "#CBD5E1", "icon": "💬"},
        "Workshop": {"bg": "#EFF6FF", "text": "#1D4ED8", "border": "#BFDBFE", "icon": "🛠️"},
        "Seminar": {"bg": "#F5F3FF", "text": "#5B21B6", "border": "#DDD6FE", "icon": "🎤"},
        "Hackathon": {"bg": "#FFF7ED", "text": "#C2410C", "border": "#FED7AA", "icon": "💻"},
        "Cultural": {"bg": "#FDF2F8", "text": "#BE185D", "border": "#FBCFE8", "icon": "🎭"},
        "Sports": {"bg": "#F0FDF4", "text": "#15803D", "border": "#BBF7D0", "icon": "🏆"},
    }
    return palette.get(category, {"bg": "#F8FAFC", "text": "#475569", "border": "#E2E8F0", "icon": "📌"})
