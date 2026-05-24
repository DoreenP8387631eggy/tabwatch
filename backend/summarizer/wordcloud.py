"""Generate word frequency data from browsing session page titles."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.session import BrowsingSession

# Common stop words to filter out
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "this", "that", "was",
    "are", "be", "been", "has", "have", "had", "not", "as", "up", "do",
    "if", "so", "we", "my", "you", "he", "she", "they", "i", "me", "us",
    "new", "how", "what", "when", "where", "who", "why", "will", "can",
    "your", "our", "their", "about", "more", "all", "also", "just", "get",
}


def _tokenize(text: str) -> list[str]:
    """Lowercase and split text into alpha tokens, filtering stop words."""
    tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def build_wordcloud(session: "BrowsingSession", top_n: int = 30) -> dict:
    """Return word frequency data derived from page titles in the session.

    Args:
        session: A BrowsingSession instance.
        top_n: Maximum number of words to return.

    Returns:
        A dict with 'words' (list of {word, count}) and 'total_words' count.
    """
    counter: Counter = Counter()

    for event in session.events:
        title = getattr(event, "title", "") or ""
        url = getattr(event, "url", "") or ""
        # Prefer title; fall back to URL path tokens
        source = title if title.strip() else url
        counter.update(_tokenize(source))

    top = counter.most_common(top_n)
    return {
        "words": [{"word": word, "count": count} for word, count in top],
        "total_words": sum(counter.values()),
        "unique_words": len(counter),
    }
