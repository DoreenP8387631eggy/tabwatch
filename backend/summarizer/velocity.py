from datetime import datetime
from typing import Dict, Any
from backend.models.session import BrowsingSession


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lstrip("www.") or url
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
            "domain_switch_sequence": [],
        }

    sorted_events = sorted(events, key=lambda e: e.timestamp)
    first_ts = _parse_ts(sorted_events[0].timestamp)
    last_ts = _parse_ts(sorted_events[-1].timestamp)
    duration_minutes = (last_ts - first_ts).total_seconds() / 60.0

    domains = [_domain(e.url) for e in sorted_events]
    switches = sum(1 for i in range(1, len(domains)) if domains[i] != domains[i - 1])
    unique_domains = len(set(domains))

    switches_per_minute = round(switches / duration_minutes, 2) if duration_minutes > 0 else 0.0

    domain_durations: Dict[str, float] = {}
    for i, event in enumerate(sorted_events):
        d = _domain(event.url)
        if i + 1 < len(sorted_events):
            next_ts = _parse_ts(sorted_events[i + 1].timestamp)
            cur_ts = _parse_ts(event.timestamp)
            secs = (next_ts - cur_ts).total_seconds()
            domain_durations[d] = domain_durations.get(d, 0.0) + secs

    avg_time = (
        round(sum(domain_durations.values()) / unique_domains, 2)
        if unique_domains > 0
        else 0.0
    )

    sequence = [domains[0]]
    for d in domains[1:]:
        if d != sequence[-1]:
            sequence.append(d)

    return {
        "total_switches": switches,
        "switches_per_minute": switches_per_minute,
        "unique_domains_visited": unique_domains,
        "avg_time_per_domain_seconds": avg_time,
        "domain_switch_sequence": sequence,
    }
