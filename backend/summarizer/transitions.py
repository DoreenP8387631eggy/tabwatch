"""Analyzes URL transition patterns within a browsing session."""

from urllib.parse import urlparse
from collections import defaultdict
from typing import Dict, List, Tuple


def _extract_domain(url: str) -> str:
    """Extract bare domain from a URL, stripping www."""
    try:
        host = urlparse(url).netloc or url
        return host.replace("www.", "").lower()
    except Exception:
        return url.lower()


def compute_transitions(session) -> Dict:
    """Compute domain-to-domain transition statistics for a session.

    Returns a dict with:
      - transition_count: total number of domain switches
      - transition_map: {from_domain: {to_domain: count}}
      - top_transitions: list of (from, to, count) sorted descending
      - self_transitions: count of events staying on the same domain
    """
    events = session.events
    if not events:
        return {
            "transition_count": 0,
            "transition_map": {},
            "top_transitions": [],
            "self_transitions": 0,
        }

    transition_map: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    self_transitions = 0
    transition_count = 0

    domains = [_extract_domain(e.url) for e in events]

    for i in range(1, len(domains)):
        src = domains[i - 1]
        dst = domains[i]
        if src == dst:
            self_transitions += 1
        else:
            transition_map[src][dst] += 1
            transition_count += 1

    # Flatten to sorted list
    top: List[Tuple[str, str, int]] = []
    for src, targets in transition_map.items():
        for dst, count in targets.items():
            top.append((src, dst, count))
    top.sort(key=lambda x: x[2], reverse=True)

    return {
        "transition_count": transition_count,
        "transition_map": {k: dict(v) for k, v in transition_map.items()},
        "top_transitions": [{"from": t[0], "to": t[1], "count": t[2]} for t in top],
        "self_transitions": self_transitions,
    }
