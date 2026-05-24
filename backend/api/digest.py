"""Blueprint exposing daily digest endpoints."""

from datetime import date

from flask import Blueprint, jsonify, request, current_app

from backend.summarizer.digest import build_daily_digest

digest_bp = Blueprint("digest", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@digest_bp.route("/digest", methods=["GET"])
def get_digest():
    """Return the daily digest for *date* query param (default: today).

    Query params:
      - date: ISO date string YYYY-MM-DD (optional)
    """
    target_date = request.args.get("date", date.today().isoformat())

    # Basic format validation
    try:
        date.fromisoformat(target_date)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    store = _store()
    all_sessions = [store.load(sid) for sid in store.list_ids()]
    all_sessions = [s for s in all_sessions if s is not None]

    digest = build_daily_digest(all_sessions, target_date)
    return jsonify(digest), 200


@digest_bp.route("/digest/today", methods=["GET"])
def get_today_digest():
    """Convenience endpoint — always returns today's digest."""
    store = _store()
    all_sessions = [store.load(sid) for sid in store.list_ids()]
    all_sessions = [s for s in all_sessions if s is not None]

    digest = build_daily_digest(all_sessions)
    return jsonify(digest), 200


def init_digest(app):
    app.register_blueprint(digest_bp, url_prefix="/api")
