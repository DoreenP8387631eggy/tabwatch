"""API routes for the badge system."""

from __future__ import annotations

from flask import Blueprint, jsonify, current_app

from backend.summarizer.badges import evaluate_badges

badges_bp = Blueprint("badges", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@badges_bp.route("/badges", methods=["GET"])
def get_badges():
    """Return all earned badges across every stored session."""
    store = _store()
    sessions = [store.load(sid) for sid in store.list_ids()]
    sessions = [s for s in sessions if s is not None]
    earned = evaluate_badges(sessions)
    return jsonify({"badges": earned, "count": len(earned)}), 200


@badges_bp.route("/badges/count", methods=["GET"])
def get_badge_count():
    """Return only the count of earned badges."""
    store = _store()
    sessions = [store.load(sid) for sid in store.list_ids()]
    sessions = [s for s in sessions if s is not None]
    earned = evaluate_badges(sessions)
    return jsonify({"count": len(earned)}), 200


def init_badges(app):
    """Register the badges blueprint with the Flask app."""
    app.register_blueprint(badges_bp)
