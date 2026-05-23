from flask import Blueprint, jsonify
from backend.storage.session_store import SessionStore

streak_bp = Blueprint("streak", __name__)
_store: SessionStore | None = None


def init_streak(store: SessionStore) -> None:
    global _store
    _store = store


@streak_bp.route("/streak", methods=["GET"])
def get_streak():
    """Return the current and longest browsing streak across all sessions."""
    from backend.summarizer.streak import compute_streak

    sessions = _store.list_all()
    result = compute_streak(sessions)
    return jsonify(result), 200


@streak_bp.route("/streak/best", methods=["GET"])
def get_best_streak():
    """Return only the longest streak ever recorded."""
    from backend.summarizer.streak import compute_streak

    sessions = _store.list_all()
    result = compute_streak(sessions)
    return jsonify({
        "longest_streak": result["longest_streak"],
        "streak_start": result["streak_start"],
    }), 200
