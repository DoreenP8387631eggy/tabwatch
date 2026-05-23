"""Alert generation based on browsing session patterns."""

from typing import List, Dict, Any
from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags

DISTRACTION_CATEGORIES = {"social", "entertainment", "news"}
DEFAULT_DISTRACTION_THRESHOLD_MINUTES = 30
DEFAULT_SESSION_DURATION_THRESHOLD_MINUTES = 120
DEFAULT_SINGLE_SITE_THRESHOLD_MINUTES = 60


def generate_alerts(
    session: BrowsingSession,
    distraction_threshold_minutes: int = DEFAULT_DISTRACTION_THRESHOLD_MINUTES,
    session_duration_threshold_minutes: int = DEFAULT_SESSION_DURATION_THRESHOLD_MINUTES,
    single_site_threshold_minutes: int = DEFAULT_SINGLE_SITE_THRESHOLD_MINUTES,
) -> List[Dict[str, Any]]:
    """Return a list of alert dicts for notable browsing patterns."""
    alerts: List[Dict[str, Any]] = []

    if not session.events:
        return alerts

    # Total session duration
    start = session.events[0].timestamp
    end = session.events[-1].timestamp
    total_minutes = (end - start) / 60

    if total_minutes >= session_duration_threshold_minutes:
        alerts.append({
            "type": "long_session",
            "severity": "warning",
            "message": f"Session has been running for {int(total_minutes)} minutes. Consider taking a break.",
        })

    # Distraction time
    tags = compute_tags(session)
    distraction_minutes = sum(
        tags.get(cat, 0) for cat in DISTRACTION_CATEGORIES
    )
    if distraction_minutes >= distraction_threshold_minutes:
        alerts.append({
            "type": "high_distraction",
            "severity": "warning",
            "message": (
                f"{int(distraction_minutes)} minutes spent on distracting sites "
                f"(social, entertainment, news)."
            ),
        })

    # Single-site dominance
    domain_time: Dict[str, float] = {}
    for i, event in enumerate(session.events[:-1]):
        next_event = session.events[i + 1]
        duration = (next_event.timestamp - event.timestamp) / 60
        domain = event.url.split("/")[2] if "://" in event.url else event.url
        domain_time[domain] = domain_time.get(domain, 0) + duration

    for domain, minutes in domain_time.items():
        if minutes >= single_site_threshold_minutes:
            alerts.append({
                "type": "single_site_dominance",
                "severity": "info",
                "message": f"Over {int(minutes)} minutes spent on {domain}.",
                "domain": domain,
            })

    return alerts
