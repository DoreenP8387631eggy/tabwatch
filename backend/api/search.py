"""API routes for searching browsing sessions."""

from __future__ import annotations

from flask import Blueprint, request, jsonify, current_app

from backend.summarizer.search import search_events, search_sessions

search_bp = Blueprint("search", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@search_bp.route("/sessions/<session_id>/search", methods=["GET"])
def search_in_session(session_id: str):
    """Search events within a single session.

    Query params:
        q     – search query (required)
        field – url | title | domain | all  (default: all)
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "query parameter 'q' is required"}), 400

    field = request.args.get("field", "all")
    if field not in ("url", "title", "domain", "all"):
        return jsonify({"error": "field must be one of: url, title, domain, all"}), 400

    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "session not found"}), 404

    hits = search_events(session, query, field=field)
    return jsonify({
        "session_id": session_id,
        "query": query,
        "field": field,
        "match_count": len(hits),
        "events": hits,
    }), 200


@search_bp.route("/search", methods=["GET"])
def search_all_sessions():
    """Search across all stored sessions.

    Query params:
        q     – search query (required)
        field – url | title | domain | all  (default: all)
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "query parameter 'q' is required"}), 400

    field = request.args.get("field", "all")
    if field not in ("url", "title", "domain", "all"):
        return jsonify({"error": "field must be one of: url, title, domain, all"}), 400

    store = _store()
    all_sessions = [store.load(sid) for sid in store.list_sessions()]
    all_sessions = [s for s in all_sessions if s is not None]

    results = search_sessions(all_sessions, query, field=field)
    return jsonify({
        "query": query,
        "field": field,
        "session_count": len(results),
        "results": results,
    }), 200
