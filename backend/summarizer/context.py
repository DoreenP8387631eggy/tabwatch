"""Context switcher: detects context switches between work, social, news, etc."""
from typing import List, Dict, Any
from backend.models.session import BrowsingSession
from backend.summarizer.tags import classify_domain
from backend.summarizer.domains import _extract_domain


def compute_context_switches(session: BrowsingSession) -> Dict[str, Any]:
    """Analyse how often the user switches between different content categories."""
    events = session.events
    if not events:
        return {
            "switches": 0,
            "sequence": [],
            "switch_rate_per_minute": 0.0,
            "dominant_context": None,
        }

    sequence: List[str] = []
    for evt in events:
        domain = _extract_domain(evt.url)
        tag = classify_domain(domain)
        if not sequence or sequence[-1] != tag:
            sequence.append(tag)

    switches = max(0, len(sequence) - 1)

    # Duration in minutes
    try:
        from datetime import datetime
        fmt = "%Y-%m-%dT%H:%M:%S"
        t_start = datetime.fromisoformat(events[0].timestamp)
        t_end = datetime.fromisoformat(events[-1].timestamp)
        duration_minutes = max((t_end - t_start).total_seconds() / 60.0, 1.0)
    except Exception:
        duration_minutes = 1.0

    switch_rate = round(switches / duration_minutes, 3)

    # Dominant context by frequency in sequence
    freq: Dict[str, int] = {}
    for ctx in sequence:
        freq[ctx] = freq.get(ctx, 0) + 1
    dominant = max(freq, key=lambda k: freq[k]) if freq else None

    return {
        "switches": switches,
        "sequence": sequence,
        "switch_rate_per_minute": switch_rate,
        "dominant_context": dominant,
        "context_frequency": freq,
    }
