"""Badge system: award badges based on browsing session history."""

from __future__ import annotations

from typing import List, Dict, Any

from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags
from backend.summarizer.focus import compute_focus

# Badge definitions: (id, name, description, check_fn)
_BADGE_DEFS: List[Dict[str, Any]] = [
    {
        "id": "first_session",
        "name": "First Steps",
        "description": "Completed your first browsing session.",
    },
    {
        "id": "focus_master",
        "name": "Focus Master",
        "description": "Achieved a focus score of 80 or above in a session.",
    },
    {
        "id": "clean_session",
        "name": "Clean Session",
        "description": "Completed a session with no social or entertainment visits.",
    },
    {
        "id": "power_user",
        "name": "Power User",
        "description": "Logged 10 or more browsing sessions.",
    },
    {
        "id": "deep_reader",
        "name": "Deep Reader",
        "description": "Spent more than 30 minutes on a single domain in a session.",
    },
]


def _check_badge(badge_id: str, sessions: List[BrowsingSession]) -> bool:
    """Return True if the badge condition is met across the given sessions."""
    closed = [s for s in sessions if s.end_time is not None]

    if badge_id == "first_session":
        return len(closed) >= 1

    if badge_id == "power_user":
        return len(closed) >= 10

    if badge_id == "focus_master":
        return any(compute_focus(s).get("score", 0) >= 80 for s in closed)

    if badge_id == "clean_session":
        for s in closed:
            tags = compute_tags(s)
            if "social" not in tags and "entertainment" not in tags:
                return True
        return False

    if badge_id == "deep_reader":
        for s in closed:
            domain_time: Dict[str, float] = {}
            events = sorted(s.events, key=lambda e: e.timestamp)
            for i, evt in enumerate(events[:-1]):
                next_ts = events[i + 1].timestamp
                duration = (next_ts - evt.timestamp).total_seconds()
                domain = evt.url.split("/")[2] if "://" in evt.url else evt.url
                domain_time[domain] = domain_time.get(domain, 0) + duration
            if any(v >= 1800 for v in domain_time.values()):
                return True
        return False

    return False


def evaluate_badges(sessions: List[BrowsingSession]) -> List[Dict[str, Any]]:
    """Return a list of earned badge dicts."""
    earned = []
    for badge in _BADGE_DEFS:
        if _check_badge(badge["id"], sessions):
            earned.append({**badge, "earned": True})
    return earned
