"""Compare two browsing sessions and highlight differences."""

from typing import Dict, Any
from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags
from backend.summarizer.summarize import summarize_session


def compare_sessions(session_a: BrowsingSession, session_b: BrowsingSession) -> Dict[str, Any]:
    """Return a structured comparison between two closed browsing sessions."""
    if not session_a.end_time or not session_b.end_time:
        raise ValueError("Both sessions must be closed before comparing.")

    summary_a = summarize_session(session_a)
    summary_b = summarize_session(session_b)
    tags_a = compute_tags(session_a)
    tags_b = compute_tags(session_b)

    duration_diff = summary_b["total_duration_seconds"] - summary_a["total_duration_seconds"]
    visits_diff = summary_b["total_visits"] - summary_a["total_visits"]
    domains_diff = summary_b["unique_domains"] - summary_a["unique_domains"]

    all_categories = set(tags_a.keys()) | set(tags_b.keys())
    category_delta: Dict[str, float] = {}
    for cat in all_categories:
        pct_a = tags_a.get(cat, 0.0)
        pct_b = tags_b.get(cat, 0.0)
        delta = round(pct_b - pct_a, 2)
        if delta != 0.0:
            category_delta[cat] = delta

    top_domains_a = set(summary_a.get("top_domains", {}).keys())
    top_domains_b = set(summary_b.get("top_domains", {}).keys())
    new_domains = sorted(top_domains_b - top_domains_a)
    dropped_domains = sorted(top_domains_a - top_domains_b)

    return {
        "session_a_id": session_a.session_id,
        "session_b_id": session_b.session_id,
        "duration_diff_seconds": duration_diff,
        "visits_diff": visits_diff,
        "unique_domains_diff": domains_diff,
        "category_percentage_delta": category_delta,
        "new_top_domains": new_domains,
        "dropped_top_domains": dropped_domains,
        "summary_a": summary_a,
        "summary_b": summary_b,
    }
