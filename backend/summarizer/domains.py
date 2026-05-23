"""Domain frequency analysis for browsing sessions."""
from collections import Counter
from urllib.parse import urlparse
from typing import Dict, List

from backend.models.session import BrowsingSession


def _extract_domain(url: str) -> str:
    """Extract the bare domain from a URL."""
    try:
        host = urlparse(url).netloc
        # strip 'www.' prefix for normalisation
        if host.startswith("www."):
            host = host[4:]
        return host or url
    except Exception:
        return url


def compute_domain_frequency(session: BrowsingSession) -> List[Dict]:
    """Return domains sorted by visit count descending.

    Each entry is a dict with keys: domain, visits, total_seconds.
    """
    visit_counts: Counter = Counter()
    time_spent: Dict[str, float] = {}

    events = sorted(session.events, key=lambda e: e.timestamp)

    for i, event in enumerate(events):
        domain = _extract_domain(event.url)
        visit_counts[domain] += 1

        # estimate time on this page as gap to next event (cap at 5 minutes)
        if i + 1 < len(events):
            delta = (events[i + 1].timestamp - event.timestamp).total_seconds()
            delta = min(delta, 300)
        else:
            delta = 0.0
        time_spent[domain] = time_spent.get(domain, 0.0) + delta

    results = [
        {
            "domain": domain,
            "visits": count,
            "total_seconds": round(time_spent.get(domain, 0.0), 1),
        }
        for domain, count in visit_counts.most_common()
    ]
    return results


def top_domains(session: BrowsingSession, n: int = 5) -> List[Dict]:
    """Return the top-n domains by visit count."""
    return compute_domain_frequency(session)[:n]
