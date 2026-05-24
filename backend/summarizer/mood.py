"""Mood inference based on browsing patterns within a session."""

from backend.models.session import BrowsingSession
from backend.summarizer.tags import classify_domain
from urllib.parse import urlparse

# Category-to-mood weight mapping
_MOOD_WEIGHTS = {
    "social": {"distracted": 2, "relaxed": 1},
    "entertainment": {"relaxed": 2, "distracted": 1},
    "news": {"anxious": 2, "curious": 1},
    "productivity": {"focused": 3},
    "development": {"focused": 3, "curious": 1},
    "education": {"curious": 2, "focused": 1},
    "shopping": {"distracted": 2, "relaxed": 1},
    "other": {"neutral": 1},
}

_ALL_MOODS = ["focused", "relaxed", "distracted", "anxious", "curious", "neutral"]


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.removeprefix("www.")
    except Exception:
        return ""


def infer_mood(session: BrowsingSession) -> dict:
    """Infer the dominant mood for a browsing session.

    Returns a dict with:
      - dominant: str  — the top mood label
      - scores: dict   — raw score per mood
      - breakdown: dict — category visit counts
    """
    scores = {m: 0 for m in _ALL_MOODS}
    breakdown: dict[str, int] = {}

    for event in session.events:
        domain = _extract_domain(event.url)
        category = classify_domain(domain)
        breakdown[category] = breakdown.get(category, 0) + 1
        weights = _MOOD_WEIGHTS.get(category, {"neutral": 1})
        for mood, weight in weights.items():
            scores[mood] = scores.get(mood, 0) + weight

    total = sum(scores.values())
    if total == 0:
        return {"dominant": "neutral", "scores": scores, "breakdown": breakdown}

    dominant = max(scores, key=lambda m: scores[m])
    normalised = {m: round(v / total, 3) for m, v in scores.items()}
    return {"dominant": dominant, "scores": normalised, "breakdown": breakdown}
