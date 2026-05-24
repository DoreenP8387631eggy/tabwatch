"""Compute browsing flow: measures how smoothly a session progresses
through topics without erratic jumping."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from backend.models.session import BrowsingSession


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return host.lstrip("www.") if host else url
    except Exception:
        return url


def compute_flow(session: "BrowsingSession") -> dict:
    """Analyse browsing flow for a session.

    Returns a dict with:
      - flow_score (0-100): higher means smoother, less erratic browsing
      - transitions: total domain transitions
      - unique_domains: number of distinct domains visited
      - revisit_rate: fraction of transitions that return to a recent domain
      - label: human-readable label (Smooth / Moderate / Erratic)
    """
    events = session.events
    if not events:
        return {
            "flow_score": 0,
            "transitions": 0,
            "unique_domains": 0,
            "revisit_rate": 0.0,
            "label": "No Data",
        }

    domains = [_extract_domain(e.url) for e in events]
    unique_domains = len(set(domains))

    transitions = 0
    revisits = 0
    window = 5  # look-back window for "revisit" detection

    for i in range(1, len(domains)):
        if domains[i] != domains[i - 1]:
            transitions += 1
            recent = domains[max(0, i - window): i]
            if domains[i] in recent:
                revisits += 1

    revisit_rate = revisits / transitions if transitions > 0 else 0.0

    # Penalise high unique-domain churn relative to session length
    churn_ratio = unique_domains / len(events)
    # Reward revisits (returning to focused topics)
    revisit_bonus = revisit_rate * 30
    base = max(0.0, 100.0 - churn_ratio * 80)
    flow_score = min(100, int(base + revisit_bonus))

    if flow_score >= 70:
        label = "Smooth"
    elif flow_score >= 40:
        label = "Moderate"
    else:
        label = "Erratic"

    return {
        "flow_score": flow_score,
        "transitions": transitions,
        "unique_domains": unique_domains,
        "revisit_rate": round(revisit_rate, 3),
        "label": label,
    }
