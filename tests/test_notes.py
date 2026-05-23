"""Integration tests for the notes API endpoints."""

import pytest
from flask import Flask

from backend.api.sessions import sessions_bp
from backend.api.notes import notes_bp
from backend.storage.session_store import SessionStore
from backend.storage.notes_store import NotesStore


@pytest.fixture()
def tmp_store(tmp_path):
    return SessionStore(data_dir=str(tmp_path)), NotesStore(data_dir=str(tmp_path))


@pytest.fixture()
def client(tmp_store):
    session_store, notes_store = tmp_store
    app = Flask(__name__)
    app.config["SESSION_STORE"] = session_store
    app.config["NOTES_STORE"] = notes_store
    app.register_blueprint(sessions_bp)
    app.register_blueprint(notes_bp)
    return app.test_client()


def _create_session(client) -> str:
    resp = client.post("/sessions")
    return resp.get_json()["id"]


def test_notes_not_found(client):
    resp = client.get("/sessions/missing/notes")
    assert resp.status_code == 404


def test_add_note_session_not_found(client):
    resp = client.post("/sessions/missing/notes", json={"text": "hi"})
    assert resp.status_code == 404


def test_add_note_empty_text(client):
    sid = _create_session(client)
    resp = client.post(f"/sessions/{sid}/notes", json={"text": ""})
    assert resp.status_code == 400


def test_add_and_get_notes(client):
    sid = _create_session(client)
    resp = client.post(f"/sessions/{sid}/notes", json={"text": "Productive morning"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["text"] == "Productive morning"
    assert data["session_id"] == sid

    resp2 = client.get(f"/sessions/{sid}/notes")
    assert resp2.status_code == 200
    notes = resp2.get_json()["notes"]
    assert len(notes) == 1
    assert notes[0]["text"] == "Productive morning"


def test_notes_summary(client):
    sid = _create_session(client)
    client.post(f"/sessions/{sid}/notes", json={"text": "First note"})
    client.post(f"/sessions/{sid}/notes", json={"text": "Second note"})
    resp = client.get(f"/sessions/{sid}/notes/summary")
    assert resp.status_code == 200
    summary = resp.get_json()["summary"]
    assert summary["count"] == 2
    assert summary["snippet"] is not None


def test_delete_notes(client):
    sid = _create_session(client)
    client.post(f"/sessions/{sid}/notes", json={"text": "To be deleted"})
    resp = client.delete(f"/sessions/{sid}/notes")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == 1
    resp2 = client.get(f"/sessions/{sid}/notes")
    assert resp2.get_json()["notes"] == []
