"""Search and filter browsing sessions by URL, domain, or title keywords."""

from __future__ import annotations

from typing import List, Dict, Any

from backend.models.session import BrowsingSession, TabEvent


def _extract_domain(url: str) -> str:
    """Extract bare domain from a URL string."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        return host.lstrip("www.").lower()
    except Exception:
        return url.lower()


def search_events(
    session: BrowsingSession,
    query: str,
    field: str = "all",
) -> List[Dict[str, Any]]:
    """Return events whose URL or title match *query* (case-insensitive).

    Args:
        session: The browsing session to search within.
        query:   The search string.
        field:   One of ``'url'``, ``'title'``, ``'domain'``, or ``'all'``.

    Returns:
        A list of matching event dicts with an added ``'domain'`` key.
    """
    q = query.strip().lower()
    if not q:
        return []

    results: List[Dict[str, Any]] = []
    for evt in session.events:
        url_lower = evt.url.lower()
        title_lower = (evt.title or "").lower()
        domain = _extract_domain(evt.url)

        match = False
        if field in ("url", "all") and q in url_lower:
            match = True
        if field in ("title", "all") and q in title_lower:
            match = True
        if field in ("domain", "all") and q in domain:
            match = True

        if match:
            row = evt.to_dict()
            row["domain"] = domain
            results.append(row)

    return results


def search_sessions(
    sessions: List[BrowsingSession],
    query: str,
    field: str = "all",
) -> List[Dict[str, Any]]:
    """Search across multiple sessions and return aggregated matches.

    Returns a list of dicts, each containing ``session_id`` and the
    matching ``events``.
    """
    q = query.strip().lower()
    if not q:
        return []

    aggregated: List[Dict[str, Any]] = []
    for session in sessions:
        hits = search_events(session, q, field=field)
        if hits:
            aggregated.append({
                "session_id": session.session_id,
                "start_time": session.start_time,
                "match_count": len(hits),
                "events": hits,
            })
    return aggregated
