"""Compute attention span metrics from a browsing session."""

from typing import Dict, Any, List
from backend.models.session import BrowsingSession

_SHALLOW_THRESHOLD = 15   # seconds — visit shorter than this is "shallow"
_DEEP_THRESHOLD = 120     # seconds — visit longer than this is "deep"


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lstrip("www.")
    except Exception:
        return url


def compute_attention(session: BrowsingSession) -> Dict[str, Any]:
    """Analyse how long the user spent on each page visit.

    Returns:
        total_visits      – number of tab events
        shallow_visits    – visits shorter than SHALLOW_THRESHOLD
        deep_visits       – visits longer than DEEP_THRESHOLD
        avg_visit_seconds – mean visit duration (seconds)
        attention_score   – 0‑100 score (higher = more sustained attention)
        longest_visit     – {domain, duration_seconds} for the longest stay
    """
    events = session.events
    if not events:
        return {
            "total_visits": 0,
            "shallow_visits": 0,
            "deep_visits": 0,
            "avg_visit_seconds": 0.0,
            "attention_score": 0,
            "longest_visit": None,
        }

    durations: List[Dict[str, Any]] = []
    for i, ev in enumerate(events):
        if i + 1 < len(events):
            try:
                from datetime import datetime
                t0 = datetime.fromisoformat(ev.timestamp)
                t1 = datetime.fromisoformat(events[i + 1].timestamp)
                secs = max(0.0, (t1 - t0).total_seconds())
            except Exception:
                secs = 0.0
        else:
            secs = 0.0
        durations.append({"domain": _extract_domain(ev.url), "seconds": secs})

    total = len(durations)
    shallow = sum(1 for d in durations if d["seconds"] < _SHALLOW_THRESHOLD)
    deep = sum(1 for d in durations if d["seconds"] >= _DEEP_THRESHOLD)
    avg = sum(d["seconds"] for d in durations) / total if total else 0.0

    # Score: penalise shallow ratio, reward deep ratio
    shallow_ratio = shallow / total if total else 0
    deep_ratio = deep / total if total else 0
    score = max(0, min(100, int((deep_ratio * 70) + ((1 - shallow_ratio) * 30))))

    longest = max(durations, key=lambda d: d["seconds"]) if durations else None

    return {
        "total_visits": total,
        "shallow_visits": shallow,
        "deep_visits": deep,
        "avg_visit_seconds": round(avg, 2),
        "attention_score": score,
        "longest_visit": longest,
    }
