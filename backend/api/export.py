"""API endpoints for exporting session data."""

from flask import Blueprint, Response, current_app, jsonify

export_bp = Blueprint("export", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@export_bp.route("/sessions/<session_id>/export/json", methods=["GET"])
def export_json(session_id: str):
    """Export a session as JSON."""
    from backend.summarizer.export import export_json as _export_json

    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    content = _export_json(session)
    return Response(
        content,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="session_{session_id}.json"'},
    )


@export_bp.route("/sessions/<session_id>/export/csv", methods=["GET"])
def export_csv(session_id: str):
    """Export a session as CSV."""
    from backend.summarizer.export import export_csv as _export_csv

    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    content = _export_csv(session)
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="session_{session_id}.csv"'},
    )


@export_bp.route("/sessions/<session_id>/export/markdown", methods=["GET"])
def export_markdown(session_id: str):
    """Export a session as a Markdown report."""
    from backend.summarizer.export import export_markdown as _export_markdown

    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    content = _export_markdown(session)
    return Response(
        content,
        mimetype="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="session_{session_id}.md"'},
    )
