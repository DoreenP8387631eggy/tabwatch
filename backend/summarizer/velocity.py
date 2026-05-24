from datetime import datetime
from typing import Dict, Any
from backend.models.session import BrowsingSession


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.utcnow()


def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        return host.lstrip("www.") if host else url
    except Exception:
        return url


def compute_velocity(session: BrowsingSession) -> Dict[str, Any]:
    """Compute tab-switching velocity metrics for a session."""
    events = session.events
    if not events:
        return {
            "total_switches": 0,
            "switches_per_minute": 0.0,
            "unique_domains_visited": 0,
            "avg_time_per_domain_seconds": 0.0,
            "most_revisited_domain": None,
            "domain_revisit_counts": {},
        }

    timestamps = [_parse_ts(e.timestamp) for e in events]
    domains = [_domain(e.url) for e in events]

    duration_seconds = (timestamps[-1] - timestamps[0]).total_seconds()
    duration_minutes = max(duration_seconds / 60.0, 1.0)

    switches = 0
    for i in range(1, len(domains)):
        if domains[i] != domains[i - 1]:
            switches += 1

    revisit_counts: Dict[str, int] = {}
    for d in domains:
        revisit_counts[d] = revisit_counts.get(d, 0) + 1

    unique_domains = len(revisit_counts)
    avg_time = duration_seconds / unique_domains if unique_domains else 0.0

    most_revisited = max(revisit_counts, key=lambda d: revisit_counts[d]) if revisit_counts else None

    return {
        "total_switches": switches,
        "switches_per_minute": round(switches / duration_minutes, 2),
        "unique_domains_visited": unique_domains,
        "avg_time_per_domain_seconds": round(avg_time, 2),
        "most_revisited_domain": most_revisited,
        "domain_revisit_counts": revisit_counts,
    }
