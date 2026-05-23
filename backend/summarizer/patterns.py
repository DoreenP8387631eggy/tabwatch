"""Detect recurring browsing patterns across multiple sessions."""

from collections import defaultdict
from typing import List, Dict, Any
from backend.models.session import BrowsingSession
from backend.summarizer.domains import _extract_domain


def _hour_bucket(ts: float) -> int:
    """Return the hour-of-day (0-23) for a Unix timestamp."""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).hour


def detect_patterns(sessions: List[BrowsingSession]) -> Dict[str, Any]:
    """Analyse a list of closed sessions and return recurring pattern data.

    Returns a dict with:
    - recurring_domains: domains visited in >= 50% of sessions
    - peak_hours: top-3 hours by total visit count across all sessions
    - avg_session_duration: mean duration in seconds
    - most_consistent_domain: domain with lowest std-dev in daily visit count
    """
    if not sessions:
        return {
            "recurring_domains": [],
            "peak_hours": [],
            "avg_session_duration": 0,
            "most_consistent_domain": None,
        }

    domain_session_hits: Dict[str, int] = defaultdict(int)
    hour_counts: Dict[int, int] = defaultdict(int)
    domain_counts_per_session: Dict[str, List[int]] = defaultdict(list)
    durations: List[float] = []

    for session in sessions:
        if session.end_time is None:
            continue
        durations.append(session.end_time - session.start_time)
        local_domain_counts: Dict[str, int] = defaultdict(int)
        for event in session.events:
            domain = _extract_domain(event.url)
            local_domain_counts[domain] += 1
            hour_counts[_hour_bucket(event.timestamp)] += 1
        for domain, count in local_domain_counts.items():
            domain_session_hits[domain] += 1
            domain_counts_per_session[domain].append(count)

    total_sessions = len([s for s in sessions if s.end_time is not None])
    if total_sessions == 0:
        return {
            "recurring_domains": [],
            "peak_hours": [],
            "avg_session_duration": 0,
            "most_consistent_domain": None,
        }

    threshold = total_sessions * 0.5
    recurring = [
        d for d, hits in domain_session_hits.items() if hits >= threshold
    ]
    recurring.sort(key=lambda d: domain_session_hits[d], reverse=True)

    peak_hours = sorted(hour_counts, key=lambda h: hour_counts[h], reverse=True)[:3]

    avg_duration = sum(durations) / len(durations) if durations else 0

    most_consistent: str | None = None
    if domain_counts_per_session:
        import statistics
        best_domain = None
        best_stdev = float("inf")
        for domain, counts in domain_counts_per_session.items():
            if len(counts) < 2:
                continue
            sd = statistics.stdev(counts)
            if sd < best_stdev:
                best_stdev = sd
                best_domain = domain
        most_consistent = best_domain

    return {
        "recurring_domains": recurring,
        "peak_hours": peak_hours,
        "avg_session_duration": round(avg_duration, 2),
        "most_consistent_domain": most_consistent,
    }
