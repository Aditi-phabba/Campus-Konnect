"""
Campus Konnect - Database & Supabase Client Service
Manages connection to Supabase PostgreSQL, Authentication, and Storage.
Handles credentials from .env and Streamlit secrets.
"""

import os
from typing import Optional, Tuple
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client, Client

# Load environment variables from local .env if present
load_dotenv()


def get_supabase_credentials() -> Tuple[str, str]:
    """Retrieve Supabase URL and Key from environment or Streamlit secrets."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")

    # Fallback to Streamlit secrets (useful when deployed on Streamlit Cloud)
    if not url and hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
    if not key and hasattr(st, "secrets") and "SUPABASE_KEY" in st.secrets:
        key = st.secrets["SUPABASE_KEY"]

    return url.strip(), key.strip()


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Optional[Client]:
    """
    Initialize and cache the Supabase client.
    Returns None if credentials are missing or connection fails.
    """
    url, key = get_supabase_credentials()
    if not url or not key:
        return None

    try:
        client: Client = create_client(url, key)
        return client
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return None


def is_supabase_configured() -> bool:
    """Check if valid Supabase credentials have been configured."""
    url, key = get_supabase_credentials()
    return bool(url and key and not url.startswith("https://your-project-id"))


# -----------------------------------------------------------------------------
# Supabase Storage Utilities
# -----------------------------------------------------------------------------

def upload_file_to_storage(
    bucket_name: str,
    destination_path: str,
    file_bytes: bytes,
    content_type: str = "application/octet-stream"
) -> Tuple[bool, str]:
    """
    Upload binary data to a Supabase Storage bucket and return the public URL.
    Returns (success, public_url_or_error_message).
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase client is not connected."

    try:
        # Upload object to bucket
        response = client.storage.from_(bucket_name).upload(
            path=destination_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        # Retrieve public URL
        public_url = client.storage.from_(bucket_name).get_public_url(destination_path)
        return True, public_url
    except Exception as e:
        err_msg = str(e)
        return False, f"Upload failed: {err_msg}"


def delete_file_from_storage(bucket_name: str, file_path: str) -> bool:
    """Delete a file from Supabase Storage."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.storage.from_(bucket_name).remove([file_path])
        return True
    except Exception:
        return False
