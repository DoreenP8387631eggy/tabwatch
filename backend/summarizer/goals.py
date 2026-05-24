"""Goal tracking: evaluate browsing sessions against user-defined productivity goals."""

from typing import Any
from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags

DEFAULT_GOALS = {
    "max_social_minutes": 30,
    "min_productive_minutes": 60,
    "max_entertainment_minutes": 45,
}

# Maps goal name prefixes to the tag they measure and how to evaluate them.
# "max" goals are met when actual <= target; "min" goals when actual >= target.
_GOAL_CONFIG: dict[str, tuple[str, str]] = {
    "max_social_minutes": ("social", "max"),
    "min_productive_minutes": ("productivity", "min"),
    "max_entertainment_minutes": ("entertainment", "max"),
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


def summarize_goals(evaluation: dict[str, Any]) -> str:
    """Return a human-readable summary string for a goal evaluation result.

    Example output:
        "2/3 goals met. FAILED: max_social_minutes (actual 45.0 min, target 30 min)."
    """
    met = evaluation["goals_met"]
    total = evaluation["goals_total"]
    failed = [r for r in evaluation["results"] if not r["met"]]

    summary = f"{met}/{total} goals met."
    if failed:
        details = "; ".join(
            f"{r['goal']} (actual {r['actual']} min, target {r['target']} min)"
            for r in failed
        )
        summary += f" FAILED: {details}."
    return summary
