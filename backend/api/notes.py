"""Flask blueprint for session notes API."""

from flask import Blueprint, jsonify, request, current_app

from backend.summarizer.notes import create_note, list_notes, summarize_notes
from backend.storage.notes_store import NotesStore

notes_bp = Blueprint("notes", __name__)


def _store() -> NotesStore:
    return current_app.config["NOTES_STORE"]


def _session_store():
    return current_app.config["SESSION_STORE"]


@notes_bp.get("/sessions/<session_id>/notes")
def get_notes(session_id: str):
    session = _session_store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    notes = _store().get_for_session(session_id)
    return jsonify({"session_id": session_id, "notes": notes})


@notes_bp.post("/sessions/<session_id>/notes")
def add_note(session_id: str):
    session = _session_store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    author = body.get("author", "user")
    try:
        note = create_note(session_id, text, author)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    saved = _store().add(note)
    return jsonify(saved), 201


@notes_bp.get("/sessions/<session_id>/notes/summary")
def get_notes_summary(session_id: str):
    session = _session_store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    notes = _store().get_for_session(session_id)
    return jsonify({"session_id": session_id, "summary": summarize_notes(notes)})


@notes_bp.delete("/sessions/<session_id>/notes")
def delete_notes(session_id: str):
    session = _session_store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    removed = _store().delete_for_session(session_id)
    return jsonify({"session_id": session_id, "deleted": removed})
