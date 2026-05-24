"""Integration tests for the /wordcloud API endpoints."""

import pytest
from datetime import datetime, timezone

from backend.app import create_app
from backend.storage.session_store import SessionStore
from backend.models.session import BrowsingSession, TabEvent


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(tmp_store, titles=None):
    now = datetime.now(timezone.utc).isoformat()
    s = BrowsingSession(session_id="sess-wc", start_time=now)
    for title in (titles or []):
        s.events.append(TabEvent(url="https://example.com", title=title, timestamp=now))
    s.end_time = now
    tmp_store.save(s)
    return s


def test_wordcloud_not_found(client):
    resp = client.get("/sessions/nonexistent/wordcloud")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Session not found"


def test_top_word_not_found(client):
    resp = client.get("/sessions/nonexistent/wordcloud/top")
    assert resp.status_code == 404


def test_wordcloud_empty_session(client, tmp_store):
    _create_session_with_events(tmp_store, titles=[])
    resp = client.get("/sessions/sess-wc/wordcloud")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["words"] == []
    assert data["total_words"] == 0


def test_wordcloud_returns_words(client, tmp_store):
    _create_session_with_events(tmp_store, titles=[
        "Python Tutorial", "Python Guide", "Advanced Python"
    ])
    resp = client.get("/sessions/sess-wc/wordcloud")
    assert resp.status_code == 200
    data = resp.get_json()
    words_dict = {w["word"]: w["count"] for w in data["words"]}
    assert words_dict.get("python") == 3
    assert data["unique_words"] >= 1


def test_wordcloud_top_n_param(client, tmp_store):
    titles = [f"topic{i} article" for i in range(20)]
    _create_session_with_events(tmp_store, titles=titles)
    resp = client.get("/sessions/sess-wc/wordcloud?top_n=3")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["words"]) <= 3


def test_top_word_returns_single(client, tmp_store):
    _create_session_with_events(tmp_store, titles=[
        "Python Tutorial", "Python Guide"
    ])
    resp = client.get("/sessions/sess-wc/wordcloud/top")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["top_word"]["word"] == "python"
    assert data["top_word"]["count"] == 2


def test_top_word_empty_session(client, tmp_store):
    _create_session_with_events(tmp_store, titles=[])
    resp = client.get("/sessions/sess-wc/wordcloud/top")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["top_word"] is None
