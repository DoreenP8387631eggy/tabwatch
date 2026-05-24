"""Scroll depth analysis for browsing sessions."""
from typing import Dict, Any
from backend.models.session import BrowsingSession
from urllib.parse import urlparse


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return host.lstrip("www.") if host else url
    except Exception:
        return url


def compute_scroll(session: BrowsingSession) -> Dict[str, Any]:
    """Analyse scroll_depth metadata across tab events.

    Each TabEvent may carry a ``scroll_depth`` key in its ``meta`` dict
    (a float 0.0–1.0 representing the fraction of the page scrolled).
    Returns aggregate statistics and per-domain averages.
    """
    if not session.events:
        return {
            "total_events": 0,
            "events_with_scroll": 0,
            "average_scroll_depth": 0.0,
            "max_scroll_depth": 0.0,
            "deep_reads": 0,
            "per_domain": {},
        }

    depths = []
    domain_depths: Dict[str, list] = {}

    for evt in session.events:
        meta = getattr(evt, "meta", {}) or {}
        depth = meta.get("scroll_depth")
        if depth is None:
            continue
        try:
            depth = float(depth)
        except (TypeError, ValueError):
            continue
        depth = max(0.0, min(1.0, depth))
        depths.append(depth)
        domain = _extract_domain(getattr(evt, "url", ""))
        domain_depths.setdefault(domain, []).append(depth)

    if not depths:
        return {
            "total_events": len(session.events),
            "events_with_scroll": 0,
            "average_scroll_depth": 0.0,
            "max_scroll_depth": 0.0,
            "deep_reads": 0,
            "per_domain": {},
        }

    avg = sum(depths) / len(depths)
    maximum = max(depths)
    deep_reads = sum(1 for d in depths if d >= 0.75)

    per_domain = {
        domain: round(sum(vals) / len(vals), 4)
        for domain, vals in domain_depths.items()
    }

    return {
        "total_events": len(session.events),
        "events_with_scroll": len(depths),
        "average_scroll_depth": round(avg, 4),
        "max_scroll_depth": round(maximum, 4),
        "deep_reads": deep_reads,
        "per_domain": per_domain,
    }
