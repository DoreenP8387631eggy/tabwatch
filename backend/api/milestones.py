"""API routes for milestone evaluation."""

from __future__ import annotations

from flask import Blueprint, jsonify

from backend.storage.session_store import SessionStore
from backend.summarizer.milestones import evaluate_milestones

_store: SessionStore | None = None

milestones_bp = Blueprint("milestones", __name__)


def init_milestones(store: SessionStore) -> None:
    global _store
    _store = store


@milestones_bp.route("/sessions/<session_id>/milestones", methods=["GET"])
def get_milestones(session_id: str):
    """Return milestones achieved in this session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    all_sessions = _store.list_all()
    total = len(all_sessions)

    achieved = evaluate_milestones(session, total_sessions=total)
    return jsonify({"session_id": session_id, "milestones": achieved})


@milestones_bp.route("/sessions/<session_id>/milestones/count", methods=["GET"])
def get_milestone_count(session_id: str):
    """Return the number of milestones achieved in this session."""
    session = _store.load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    all_sessions = _store.list_all()
    total = len(all_sessions)

    achieved = evaluate_milestones(session, total_sessions=total)
    return jsonify({"session_id": session_id, "count": len(achieved)})
