"""
Campus Konnect - Smart Campus Feed Recommendation Service
=============================================================================
RULE-BASED RECOMMENDATION ENGINE (ACADEMIC VIVA / DEMONSTRATION READY)
=============================================================================
NOTE: This is intentionally a transparent, rule-based heuristic scoring engine,
NOT a black-box Machine Learning model. It prioritizes campus updates, events,
and academic resources according to each student's profile attributes:
  1. Primary Department (e.g., Computer Science, Data Science)
  2. Academic Year (e.g., Year 1 vs Year 4)
  3. Stated Student Interests (e.g., AI, Hackathons, Placements, Web Dev)
  4. Recency (freshness of publication)

SCORING HEURISTICS:
  - Official Announcement / Pinned: +5 points (urgent campus notices)
  - Interest Match in Category or Content: +3 points
  - Department Affinity: +2 points
  - Senior Year Career / Placement Boost (Year 3/4): +2 points
  - Fresher Academic Orientation Boost (Year 1): +2 points
  - Content Recency (< 48 hours): +1 point

Content items are sorted descending by calculated Relevance Score.
=============================================================================
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from utils.helpers import parse_datetime


def calculate_post_relevance_score(post: Dict[str, Any], user_profile: Optional[Dict[str, Any]]) -> float:
    """
    Compute a numerical recommendation score for a given post relative to a student's profile.
    
    Explanation for Project Viva:
    -----------------------------
    We evaluate multiple dimensions of profile alignment:
      - Is it an administrative pinned announcement?
      - Does the post content contain keywords matching the student's declared interests?
      - Does the post category cater to the student's current academic year focus?
    """
    if not user_profile:
        # Default fallback scoring based solely on pinned state and recency
        score = 0.0
        if post.get("is_pinned"):
            score += 5.0
        return score

    score = 0.0

    user_dept = (user_profile.get("department") or "").lower()
    user_year = user_profile.get("year", 1)
    user_interests = [i.lower() for i in (user_profile.get("interests") or [])]

    category = (post.get("category") or "").lower()
    title = (post.get("title") or "").lower()
    content = (post.get("content") or "").lower()
    combined_text = f"{title} {content} {category}"

    author = post.get("author") or {}
    author_dept = (author.get("department") or "").lower()

    # 1. Official Announcements and Pinned Notices (+5.0)
    # Administrative updates must be visible to all campus students regardless of major.
    if post.get("is_pinned") or post.get("is_announcement") or category == "announcement":
        score += 5.0

    # 2. Interest Alignment (+3.0 per matching interest)
    # Check if student's declared interests appear in post title, category, or body
    for interest in user_interests:
        if interest in combined_text:
            score += 3.0
            break  # Cap single category-level interest match to prevent runaway score

    # 3. Department Affinity (+2.0)
    # Posts published by peers or faculty within the same department have higher local relevance.
    if author_dept and user_dept and (author_dept == user_dept or user_dept in author_dept):
        score += 2.0

    # 4. Academic Year Tailoring (+2.0)
    # 3rd & 4th year students need Placements & Opportunities; Freshmen need Academics & Clubs
    if user_year in [3, 4, 5]:
        if category in ["placement", "opportunity"]:
            score += 2.5
    elif user_year == 1:
        if category in ["academic", "club", "event"]:
            score += 2.0

    # 5. Content Freshness & Recency (+1.0)
    # Give priority to items published within the last 48 hours
    created_dt = parse_datetime(post.get("created_at"))
    if created_dt:
        now = datetime.now(timezone.utc)
        if (now - created_dt) <= timedelta(days=2):
            score += 1.0

    # 6. Engagement Signals (+0.5 for active discussions/likes)
    likes_count = post.get("likes_count", 0)
    comments_count = post.get("comments_count", 0)
    if likes_count >= 5 or comments_count >= 3:
        score += 0.5

    return round(score, 2)


def rank_posts_for_smart_feed(
    posts: List[Dict[str, Any]],
    user_profile: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Sort a list of posts according to their calculated Smart Feed recommendation score.
    Injects '_smart_score' attribute into each post for UI display/debugging.
    """
    if not posts:
        return []

    for post in posts:
        score = calculate_post_relevance_score(post, user_profile)
        post["_smart_score"] = score

    # Sort descending by smart score; ties broken by created_at
    ranked = sorted(
        posts,
        key=lambda p: (p.get("_smart_score", 0.0), str(p.get("created_at", ""))),
        reverse=True
    )
    return ranked


def rank_events_for_user(
    events: List[Dict[str, Any]],
    user_profile: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Score and prioritize events matching student interests (e.g., Hackathons, Workshops, Placements).
    """
    if not events:
        return []

    if not user_profile:
        return events

    user_interests = [i.lower() for i in (user_profile.get("interests") or [])]
    user_year = user_profile.get("year", 1)

    for event in events:
        score = 0.0
        cat = (event.get("category") or "").lower()
        title = (event.get("title") or "").lower()
        desc = (event.get("description") or "").lower()
        text = f"{title} {desc} {cat}"

        for interest in user_interests:
            if interest in text:
                score += 3.0
                break

        if user_year in [3, 4] and cat in ["hackathon", "placement", "workshop"]:
            score += 2.0
        elif user_year == 1 and cat in ["club", "cultural", "sports"]:
            score += 2.0

        event["_smart_score"] = round(score, 2)

    return sorted(events, key=lambda e: e.get("_smart_score", 0.0), reverse=True)


def rank_resources_for_user(
    resources: List[Dict[str, Any]],
    user_profile: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Score and prioritize academic resources matching student's department and semester.
    """
    if not resources or not user_profile:
        return resources

    user_dept = (user_profile.get("department") or "").lower()
    user_year = user_profile.get("year", 1)
    # Estimate current semesters for the student's year (e.g. Year 2 -> Sem 3 or 4)
    expected_sems = [user_year * 2 - 1, user_year * 2]

    for res in resources:
        score = 0.0
        r_dept = (res.get("department") or "").lower()
        r_sem = res.get("semester", 0)

        if r_dept and user_dept and (r_dept == user_dept or user_dept in r_dept):
            score += 4.0

        if r_sem in expected_sems:
            score += 3.0

        res["_smart_score"] = round(score, 2)

    return sorted(resources, key=lambda r: r.get("_smart_score", 0.0), reverse=True)
