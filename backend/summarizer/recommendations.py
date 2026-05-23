"""Generate productivity recommendations based on browsing session data."""

from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags
from backend.summarizer.goals import evaluate_goals


DISTRACTION_THRESHOLD = 0.4  # 40% distraction triggers a warning
FOCUS_MIN_MINUTES = 25       # Minimum focused block length to praise
SHORT_SESSION_MINUTES = 10   # Sessions shorter than this get a nudge


def generate_recommendations(session: BrowsingSession) -> list[dict]:
    """Return a list of recommendation dicts for the given closed session."""
    if not session.end_time:
        return [{"level": "info", "message": "Session is still open — close it to get recommendations."}]

    recommendations = []
    events = session.events

    if not events:
        recommendations.append({
            "level": "info",
            "message": "No browsing events recorded in this session."
        })
        return recommendations

    # --- Duration check ---
    total_seconds = (session.end_time - session.start_time).total_seconds()
    total_minutes = total_seconds / 60

    if total_minutes < SHORT_SESSION_MINUTES:
        recommendations.append({
            "level": "info",
            "message": f"Short session ({total_minutes:.0f} min). Consider longer focused work blocks."
        })

    # --- Distraction ratio ---
    tags = compute_tags(session)
    total_time = sum(t["minutes"] for t in tags)
    distraction_time = next((t["minutes"] for t in tags if t["category"] == "social"), 0)
    distraction_time += next((t["minutes"] for t in tags if t["category"] == "entertainment"), 0)

    if total_time > 0:
        distraction_ratio = distraction_time / total_time
        if distraction_ratio >= DISTRACTING_THRESHOLD:
            recommendations.append({
                "level": "warning",
                "message": (
                    f"{distraction_ratio:.0%} of your session was spent on distracting sites. "
                    "Try using a site blocker during focus time."
                )
            })
        elif distraction_ratio == 0:
            recommendations.append({
                "level": "success",
                "message": "Great job! No time spent on distracting sites this session."
            })

    # --- Goals check ---
    goals = evaluate_goals(session)
    unmet = [g for g in goals if not g["met"]]
    if unmet:
        for g in unmet:
            recommendations.append({
                "level": "warning",
                "message": f"Goal not met: {g['label']} — {g['actual_minutes']:.0f}/{g['target_minutes']} min."
            })
    else:
        recommendations.append({
            "level": "success",
            "message": "All productivity goals met for this session. Keep it up!"
        })

    return recommendations
