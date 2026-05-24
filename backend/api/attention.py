"""Flask blueprint for attention-span endpoints."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.attention import compute_attention

attention_bp = Blueprint("attention", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


def init_attention(app, store):
    app.config["SESSION_STORE"] = store
    app.register_blueprint(attention_bp, url_prefix="/sessions")


@attention_bp.route("/<session_id>/attention", methods=["GET"])
def get_attention(session_id: str):
    """Return full attention metrics for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    return jsonify(compute_attention(session))


@attention_bp.route("/<session_id>/attention/score", methods=["GET"])
def get_attention_score(session_id: str):
    """Return only the attention score (0-100) for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    result = compute_attention(session)
    return jsonify({"session_id": session_id, "attention_score": result["attention_score"]})


@attention_bp.route("/<session_id>/attention/longest", methods=["GET"])
def get_longest_visit(session_id: str):
    """Return the domain and duration of the longest single visit."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404
    result = compute_attention(session)
    longest = result.get("longest_visit")
    if longest is None:
        return jsonify({"error": "no visits recorded"}), 404
    return jsonify({"session_id": session_id, "longest_visit": longest})
