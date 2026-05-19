"""Goal tracking: evaluate browsing sessions against user-defined productivity goals."""

from typing import Any
from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags

DEFAULT_GOALS = {
    "max_social_minutes": 30,
    "min_productive_minutes": 60,
    "max_entertainment_minutes": 45,
}


def evaluate_goals(
    session: BrowsingSession, goals: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Evaluate a closed session against productivity goals.

    Returns a dict with each goal, its target, actual value, and whether it was met.
    """
    if goals is None:
        goals = DEFAULT_GOALS

    tags = compute_tags(session)
    tag_minutes = {tag: round(secs / 60, 2) for tag, secs in tags.items()}

    results: list[dict[str, Any]] = []

    if "max_social_minutes" in goals:
        actual = tag_minutes.get("social", 0.0)
        target = goals["max_social_minutes"]
        results.append({
            "goal": "max_social_minutes",
            "target": target,
            "actual": actual,
            "met": actual <= target,
        })

    if "min_productive_minutes" in goals:
        actual = tag_minutes.get("productivity", 0.0)
        target = goals["min_productive_minutes"]
        results.append({
            "goal": "min_productive_minutes",
            "target": target,
            "actual": actual,
            "met": actual >= target,
        })

    if "max_entertainment_minutes" in goals:
        actual = tag_minutes.get("entertainment", 0.0)
        target = goals["max_entertainment_minutes"]
        results.append({
            "goal": "max_entertainment_minutes",
            "target": target,
            "actual": actual,
            "met": actual <= target,
        })

    goals_met = sum(1 for r in results if r["met"])
    return {
        "goals_met": goals_met,
        "goals_total": len(results),
        "all_met": goals_met == len(results),
        "results": results,
    }
