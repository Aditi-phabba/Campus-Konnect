"""
Campus Konnect - Authentication Service
Handles user registration, login, session state, profile synchronization, and logout.
"""

from typing import Optional, Tuple, Dict, Any, List
import streamlit as st
from services.database import get_supabase_client


def sign_up(
    email: str,
    password: str,
    full_name: str,
    department: str,
    year: int,
    interests: List[str],
    bio: str = ""
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Register a new student with Supabase Auth and initialize their public profile.
    """
    client = get_supabase_client()
    if not client:
        return False, "Database connection not configured. Please check your .env settings.", None

    clean_email = email.strip().lower()
    user_metadata = {
        "full_name": full_name.strip(),
        "department": department,
        "year": int(year),
        "interests": interests or [],
        "bio": bio.strip(),
        "role": "student"
    }

    try:
        # Call Supabase Auth sign up
        response = client.auth.sign_up({
            "email": clean_email,
            "password": password,
            "options": {
                "data": user_metadata
            }
        })

        if not response.user:
            return False, "Registration failed: No user returned from authentication service.", None

        user_id = response.user.id

        # Guarantee profile record in 'profiles' table
        profile_data = {
            "id": user_id,
            "email": clean_email,
            "full_name": full_name.strip(),
            "department": department,
            "year": int(year),
            "interests": interests or [],
            "bio": bio.strip(),
            "role": "student"
        }

        try:
            client.table("profiles").upsert(profile_data).execute()
        except Exception as pe:
            # The trigger might have already created it
            print(f"Profile upsert notice: {pe}")

        # Check if email confirmation is required by Supabase
        if not response.session:
            return (
                True,
                "Registration successful! Please check your email inbox to verify your account before logging in, or log in if confirmation is disabled.",
                profile_data
            )

        # If session is active immediately
        set_session_user(profile_data)
        return True, "Account created successfully! Welcome to Campus Konnect.", profile_data

    except Exception as e:
        err = str(e)
        if "already registered" in err.lower() or "unique constraint" in err.lower():
            return False, "An account with this email address already exists.", None
        return False, f"Registration error: {err}", None


def sign_in(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate an existing user, verify their profile, and store session in state.
    """
    client = get_supabase_client()
    if not client:
        return False, "Database connection not configured.", None

    clean_email = email.strip().lower()

    try:
        response = client.auth.sign_in_with_password({
            "email": clean_email,
            "password": password
        })

        if not response.user:
            return False, "Invalid email or password.", None

        user_id = response.user.id

        # Fetch authoritative user profile from database
        prof_res = client.table("profiles").select("*").eq("id", user_id).execute()
        profile = None

        if prof_res.data and len(prof_res.data) > 0:
            profile = prof_res.data[0]
        else:
            # Fallback if profile row is not yet created
            meta = response.user.user_metadata or {}
            profile = {
                "id": user_id,
                "email": clean_email,
                "full_name": meta.get("full_name", clean_email.split("@")[0]),
                "department": meta.get("department", "Computer Science & Engineering"),
                "year": meta.get("year", 1),
                "interests": meta.get("interests", []),
                "bio": meta.get("bio", ""),
                "role": meta.get("role", "student"),
                "avatar_url": meta.get("avatar_url", "")
            }
            try:
                client.table("profiles").insert(profile).execute()
            except Exception:
                pass

        set_session_user(profile)
        return True, "Login successful!", profile

    except Exception as e:
        err = str(e)
        if "invalid login credentials" in err.lower() or "invalid_grant" in err.lower():
            return False, "Invalid email or password.", None
        if "email not confirmed" in err.lower():
            return False, "Email address not verified yet. Please check your inbox.", None
        return False, f"Authentication error: {err}", None


def sign_out() -> None:
    """Log out current user and clear local session state."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    for key in ["authenticated", "user", "active_page", "post_cache"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["authenticated"] = False
    st.session_state["user"] = None


def set_session_user(profile: Dict[str, Any]) -> None:
    """Store profile in Streamlit session state."""
    st.session_state["authenticated"] = True
    st.session_state["user"] = profile


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the currently logged-in user profile dictionary, or None."""
    if not st.session_state.get("authenticated", False):
        return None
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """Return True if user is currently authenticated."""
    return bool(st.session_state.get("authenticated", False) and st.session_state.get("user"))


def is_admin_user() -> bool:
    """Verify if the current user has the admin role."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "admin"


def refresh_user_profile() -> Optional[Dict[str, Any]]:
    """Fetch the latest user profile from the database and refresh session state."""
    user = get_current_user()
    if not user:
        return None

    client = get_supabase_client()
    if not client:
        return user

    try:
        res = client.table("profiles").select("*").eq("id", user["id"]).execute()
        if res.data and len(res.data) > 0:
            latest = res.data[0]
            st.session_state["user"] = latest
            return latest
    except Exception as e:
        print(f"Error refreshing profile: {e}")
    return user
