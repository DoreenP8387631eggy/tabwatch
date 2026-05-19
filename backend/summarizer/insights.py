"""Generate productivity insights from a browsing session."""

from collections import defaultdict
from datetime import timedelta
from typing import Any

from backend.models.session import BrowsingSession
from backend.summarizer.tags import classify_domain, compute_tags
from backend.summarizer.summarize import _extract_domain


def _format_duration(seconds: float) -> str:
    """Return a human-readable duration string."""
    td = timedelta(seconds=int(seconds))
    total_minutes = int(td.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def generate_insights(session: BrowsingSession) -> dict[str, Any]:
    """Produce productivity insights for a closed session."""
    events = session.events
    if not events:
        return {"session_id": session.session_id, "insights": [], "score": None}

    domain_time: dict[str, float] = defaultdict(float)
    for i, event in enumerate(events):
        if i + 1 < len(events):
            duration = (
                events[i + 1].timestamp - event.timestamp
            ).total_seconds()
            domain = _extract_domain(event.url)
            domain_time[domain] += max(duration, 0)

    total_time = sum(domain_time.values()) or 1
    tags = compute_tags(events)

    productive_ratio = tags.get("productive", 0) / 100
    distracted_ratio = tags.get("social", 0) / 100 + tags.get("entertainment", 0) / 100
    score = max(0, min(100, int((productive_ratio - distracted_ratio * 0.5) * 100)))

    top_domains = sorted(domain_time.items(), key=lambda x: x[1], reverse=True)[:3]

    insights = []

    if productive_ratio >= 0.6:
        insights.append("Great focus session — majority of time spent on productive sites.")
    elif distracted_ratio >= 0.5:
        insights.append("High distraction detected — consider limiting social/entertainment sites.")
    else:
        insights.append("Mixed session with varied browsing activity.")

    if top_domains:
        top_name, top_secs = top_domains[0]
        insights.append(
            f"Most visited domain: {top_name} ({_format_duration(top_secs)})"
        )

    session_duration = (events[-1].timestamp - events[0].timestamp).total_seconds()
    insights.append(f"Total active session time: {_format_duration(session_duration)}")

    return {
        "session_id": session.session_id,
        "score": score,
        "duration_seconds": int(session_duration),
        "top_domains": [
            {"domain": d, "seconds": int(s), "readable": _format_duration(s)}
            for d, s in top_domains
        ],
        "tag_breakdown": tags,
        "insights": insights,
    }
