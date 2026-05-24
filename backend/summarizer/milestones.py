"""Milestone detection: reward users when they hit browsing productivity targets."""

from __future__ import annotations

from typing import Any

from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags

_MILESTONES = [
    {
        "id": "first_session",
        "title": "First Step",
        "description": "Completed your first browsing session.",
        "condition": lambda stats: stats["total_sessions"] >= 1,
    },
    {
        "id": "ten_sessions",
        "title": "Getting Started",
        "description": "Completed 10 browsing sessions.",
        "condition": lambda stats: stats["total_sessions"] >= 10,
    },
    {
        "id": "focus_hour",
        "title": "Deep Focus",
        "description": "Spent at least 60 minutes on productive sites in a single session.",
        "condition": lambda stats: stats["productive_minutes"] >= 60,
    },
    {
        "id": "low_distraction",
        "title": "Stay on Track",
        "description": "Less than 10% of session time on social/entertainment sites.",
        "condition": lambda stats: stats["distraction_pct"] < 10,
    },
    {
        "id": "domain_explorer",
        "title": "Domain Explorer",
        "description": "Visited 20 or more unique domains in a single session.",
        "condition": lambda stats: stats["unique_domains"] >= 20,
    },
]


def _session_stats(session: BrowsingSession) -> dict[str, Any]:
    """Derive stats needed for milestone evaluation from a single session."""
    events = session.events
    if not events:
        return {"productive_minutes": 0, "distraction_pct": 0.0, "unique_domains": 0, "total_sessions": 1}

    tags = compute_tags(session)
    total_sec = sum(e.duration for e in events if e.duration)
    prod_sec = tags.get("productive", 0)
    dist_sec = tags.get("social", 0) + tags.get("entertainment", 0)

    unique_domains = len({e.url.split("/")[2] for e in events if e.url and "/" in e.url})

    return {
        "productive_minutes": prod_sec / 60,
        "distraction_pct": (dist_sec / total_sec * 100) if total_sec else 0.0,
        "unique_domains": unique_domains,
        "total_sessions": 1,
    }


def evaluate_milestones(session: BrowsingSession, total_sessions: int = 1) -> list[dict[str, Any]]:
    """Return list of achieved milestone dicts for the given session."""
    stats = _session_stats(session)
    stats["total_sessions"] = total_sessions

    achieved = []
    for m in _MILESTONES:
        if m["condition"](stats):
            achieved.append({
                "id": m["id"],
                "title": m["title"],
                "description": m["description"],
                "achieved": True,
            })
    return achieved
