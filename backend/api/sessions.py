from datetime import datetime
from flask import Blueprint, jsonify, request

from backend.models.session import BrowsingSession, TabEvent
from backend.storage.session_store import SessionStore

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")
store = SessionStore()


@sessions_bp.route("/", methods=["POST"])
def create_session():
    session = BrowsingSession()
    store.save(session)
    return jsonify(session.to_dict()), 201


@sessions_bp.route("/", methods=["GET"])
def list_sessions():
    session_ids = store.list_sessions()
    return jsonify({"sessions": session_ids}), 200


@sessions_bp.route("/<session_id>", methods=["GET"])
def get_session(session_id: str):
    session = store.load(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session.to_dict()), 200


@sessions_bp.route("/<session_id>/events", methods=["POST"])
def add_event(session_id: str):
    session = store.load(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    body = request.get_json()
    required = {"url", "title", "event_type"}
    if not body or not required.issubset(body.keys()):
        return jsonify({"error": f"Missing fields: {required}"}), 400

    event = TabEvent(
        url=body["url"],
        title=body["title"],
        timestamp=datetime.utcnow(),
        event_type=body["event_type"],
        duration_seconds=body.get("duration_seconds"),
    )
    session.add_event(event)
    store.save(session)
    return jsonify(event.to_dict()), 201


@sessions_bp.route("/<session_id>/close", methods=["POST"])
def close_session(session_id: str):
    session = store.load(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    session.close()
    store.save(session)
    return jsonify(session.to_dict()), 200
