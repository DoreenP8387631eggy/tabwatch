"""Unit tests for backend/summarizer/wordcloud.py."""

from datetime import datetime, timezone

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.wordcloud import _tokenize, build_wordcloud


def _make_session(events=None):
    s = BrowsingSession(session_id="s1", start_time=datetime.now(timezone.utc).isoformat())
    for ev in (events or []):
        s.events.append(ev)
    return s


def _evt(url="https://example.com", title=""):
    return TabEvent(url=url, title=title, timestamp=datetime.now(timezone.utc).isoformat())


# --- _tokenize ---

def test_tokenize_basic():
    tokens = _tokenize("Hello World")
    assert "hello" in tokens
    assert "world" in tokens


def test_tokenize_removes_stop_words():
    tokens = _tokenize("the quick brown fox")
    assert "the" not in tokens
    assert "quick" in tokens
    assert "brown" in tokens


def test_tokenize_ignores_short_words():
    # Words shorter than 3 chars should be excluded
    tokens = _tokenize("go do it")
    assert tokens == []


def test_tokenize_lowercases():
    tokens = _tokenize("Python DEVELOPER")
    assert "python" in tokens
    assert "developer" in tokens


# --- build_wordcloud ---

def test_wordcloud_empty_session():
    s = _make_session()
    result = build_wordcloud(s)
    assert result["words"] == []
    assert result["total_words"] == 0
    assert result["unique_words"] == 0


def test_wordcloud_counts_title_words():
    s = _make_session([
        _evt(title="Python Tutorial"),
        _evt(title="Python Guide"),
    ])
    result = build_wordcloud(s)
    words_dict = {w["word"]: w["count"] for w in result["words"]}
    assert words_dict.get("python") == 2
    assert words_dict.get("tutorial") == 1
    assert words_dict.get("guide") == 1


def test_wordcloud_top_n_respected():
    titles = [f"unique{i} word" for i in range(20)]
    s = _make_session([_evt(title=t) for t in titles])
    result = build_wordcloud(s, top_n=5)
    assert len(result["words"]) <= 5


def test_wordcloud_falls_back_to_url():
    s = _make_session([_evt(url="https://example.com/python/tutorial", title="")])
    result = build_wordcloud(s)
    words_dict = {w["word"]: w["count"] for w in result["words"]}
    # URL tokens like 'python', 'tutorial', 'example', 'https', 'com' may appear
    assert result["total_words"] > 0
