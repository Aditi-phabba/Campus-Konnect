"""
Campus Konnect - Input Validation Utilities
Provides robust validation functions for user authentication, posts, events, and file uploads.
"""

import re
from typing import Tuple, List

# Basic regex for university/email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    if not email or not email.strip():
        return False, "Email address is required."
    clean = email.strip()
    if not EMAIL_REGEX.match(clean):
        return False, "Please enter a valid email address (e.g., student@college.edu)."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength (at least 6 characters for Supabase Auth compatibility)."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""


def validate_passwords_match(password: str, confirm_password: str) -> Tuple[bool, str]:
    """Validate that password and confirm password match."""
    valid_p, err = validate_password(password)
    if not valid_p:
        return False, err
    if password != confirm_password:
        return False, "Passwords do not match."
    return True, ""


def validate_required_text(
    text: str,
    field_name: str,
    min_len: int = 1,
    max_len: int = 5000
) -> Tuple[bool, str]:
    """Validate non-empty string and length constraints."""
    if text is None or not text.strip():
        return False, f"{field_name} is required."
    cleaned = text.strip()
    if len(cleaned) < min_len:
        return False, f"{field_name} must be at least {min_len} characters long."
    if len(cleaned) > max_len:
        return False, f"{field_name} cannot exceed {max_len} characters."
    return True, ""


def validate_file_upload(
    file_name: str,
    file_size_bytes: int,
    allowed_extensions: List[str],
    max_size_mb: int
) -> Tuple[bool, str]:
    """Validate file extension and file size constraints."""
    if not file_name:
        return False, "File name is missing."

    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if not extension or extension not in [ext.lower() for ext in allowed_extensions]:
        allowed_str = ", ".join([f".{ext}" for ext in allowed_extensions])
        return False, f"Unsupported file type (.{extension}). Allowed formats: {allowed_str}"

    max_bytes = max_size_mb * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File size exceeds maximum allowed limit of {max_size_mb} MB."

    return True, ""
