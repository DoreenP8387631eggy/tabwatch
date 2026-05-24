"""Daily digest: aggregate multiple sessions into a single summary report."""

from datetime import date, datetime
from typing import List, Dict, Any

from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags
from backend.summarizer.domains import compute_domain_frequency, top_domains
from backend.summarizer.insights import generate_insights


def _session_date(session: BrowsingSession) -> str:
    """Return the ISO date string (YYYY-MM-DD) for a session's start time."""
    dt = datetime.fromisoformat(session.start_time)
    return dt.date().isoformat()


def build_daily_digest(sessions: List[BrowsingSession], target_date: str | None = None) -> Dict[str, Any]:
    """Aggregate all sessions for *target_date* (defaults to today) into a digest.

    Returns a dict with:
      - date: the target date
      - session_count: number of sessions included
      - total_duration_seconds: combined duration
      - top_domains: top-5 domains across all sessions
      - tag_totals: merged tag time totals (seconds)
      - highlights: list of notable insight strings
    """
    if target_date is None:
        target_date = date.today().isoformat()

    day_sessions = [
        s for s in sessions
        if s.end_time is not None and _session_date(s) == target_date
    ]

    if not day_sessions:
        return {
            "date": target_date,
            "session_count": 0,
            "total_duration_seconds": 0,
            "top_domains": [],
            "tag_totals": {},
            "highlights": ["No completed sessions found for this date."],
        }

    total_duration = sum(
        (
            datetime.fromisoformat(s.end_time) - datetime.fromisoformat(s.start_time)
        ).total_seconds()
        for s in day_sessions
    )

    # Merge domain frequencies
    merged_freq: Dict[str, int] = {}
    for s in day_sessions:
        for domain, count in compute_domain_frequency(s).items():
            merged_freq[domain] = merged_freq.get(domain, 0) + count
    domains_top = top_domains(merged_freq, n=5)

    # Merge tag totals
    merged_tags: Dict[str, float] = {}
    for s in day_sessions:
        tags = compute_tags(s)
        for tag, seconds in tags.items():
            merged_tags[tag] = merged_tags.get(tag, 0.0) + seconds

    # Collect highlights from each session's insights
    highlights = []
    for s in day_sessions:
        info = generate_insights(s)
        for msg in info.get("insights", []):
            if msg not in highlights:
                highlights.append(msg)

    return {
        "date": target_date,
        "session_count": len(day_sessions),
        "total_duration_seconds": round(total_duration),
        "top_domains": domains_top,
        "tag_totals": {k: round(v) for k, v in merged_tags.items()},
        "highlights": highlights or ["Nothing notable to report."],
    }
