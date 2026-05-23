"""Integration tests for session export endpoints."""

import json
import os
import tempfile

import pytest

from backend.app import create_app
from backend.storage.session_store import SessionStore


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    app = create_app(tmp_store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _create_session_with_events(client):
    resp = client.post("/sessions", json={"label": "export-test"})
    session_id = resp.get_json()["session_id"]
    for url, title in [
        ("https://github.com/user/repo", "GitHub Repo"),
        ("https://news.ycombinator.com", "Hacker News"),
        ("https://docs.python.org/3/", "Python Docs"),
    ]:
        client.post(
            f"/sessions/{session_id}/events",
            json={"url": url, "title": title, "duration_seconds": 120, "event_type": "visit"},
        )
    client.post(f"/sessions/{session_id}/close")
    return session_id


def test_export_not_found_json(client):
    resp = client.get("/sessions/missing/export/json")
    assert resp.status_code == 404


def test_export_not_found_csv(client):
    resp = client.get("/sessions/missing/export/csv")
    assert resp.status_code == 404


def test_export_not_found_markdown(client):
    resp = client.get("/sessions/missing/export/markdown")
    assert resp.status_code == 404


def test_export_json(client):
    sid = _create_session_with_events(client)
    resp = client.get(f"/sessions/{sid}/export/json")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"
    data = json.loads(resp.data)
    assert data["session_id"] == sid
    assert "summary" in data
    assert "tags" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) == 3


def test_export_csv(client):
    sid = _create_session_with_events(client)
    resp = client.get(f"/sessions/{sid}/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.content_type
    text = resp.data.decode()
    lines = [l for l in text.splitlines() if l.strip()]
    assert lines[0].startswith("timestamp")
    assert len(lines) == 4  # header + 3 events
    assert "github.com" in text


def test_export_markdown(client):
    sid = _create_session_with_events(client)
    resp = client.get(f"/sessions/{sid}/export/markdown")
    assert resp.status_code == 200
    assert "text/markdown" in resp.content_type
    text = resp.data.decode()
    assert "# Browsing Session Report" in text
    assert sid in text
    assert "## Summary" in text
    assert "## Tags" in text
    assert "## Top Domains" in text
