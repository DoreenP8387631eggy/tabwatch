"""Productivity score computation for browsing sessions."""

from __future__ import annotations

from typing import Any

from backend.models.session import BrowsingSession
from backend.summarizer.tags import compute_tags

# Weight map: how much each category contributes to productivity
_CATEGORY_WEIGHTS: dict[str, float] = {
    "work": 1.0,
    "development": 1.0,
    "education": 0.8,
    "reference": 0.6,
    "news": 0.2,
    "social": -0.3,
    "entertainment": -0.5,
    "other": 0.0,
}


def compute_productivity(session: BrowsingSession) -> dict[str, Any]:
    """Return a productivity breakdown and overall score (0–100) for a session."""
    if not session.events:
        return {
            "score": 0,
            "label": "no data",
            "breakdown": {},
            "total_events": 0,
        }

    tags = compute_tags(session)
    total = sum(tags.values()) or 1  # avoid division by zero

    weighted_sum = 0.0
    breakdown: dict[str, dict[str, Any]] = {}

    for category, count in tags.items():
        weight = _CATEGORY_WEIGHTS.get(category, 0.0)
        proportion = count / total
        contribution = weight * proportion
        weighted_sum += contribution
        breakdown[category] = {
            "count": count,
            "proportion": round(proportion, 3),
            "weight": weight,
            "contribution": round(contribution, 3),
        }

    # Normalise to 0–100; raw weighted_sum is in [-1, 1]
    raw_score = (weighted_sum + 1) / 2  # shift to [0, 1]
    score = round(raw_score * 100)

    if score >= 70:
        label = "productive"
    elif score >= 45:
        label = "neutral"
    else:
        label = "distracted"

    return {
        "score": score,
        "label": label,
        "breakdown": breakdown,
        "total_events": len(session.events),
    }
