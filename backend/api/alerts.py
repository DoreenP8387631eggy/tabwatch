"""API routes for browsing session alerts."""

from flask import Blueprint, jsonify, current_app
from backend.summarizer.alerts import generate_alerts

alerts_bp = Blueprint("alerts", __name__)


def _store():
    return current_app.config["SESSION_STORE"]


@alerts_bp.route("/sessions/<session_id>/alerts", methods=["GET"])
def get_alerts(session_id: str):
    """Return all alerts for a given session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    alerts = generate_alerts(session)
    return jsonify({
        "session_id": session_id,
        "alert_count": len(alerts),
        "alerts": alerts,
    })


@alerts_bp.route("/sessions/<session_id>/alerts/summary", methods=["GET"])
def get_alerts_summary(session_id: str):
    """Return a high-level summary of alert severities for a session."""
    session = _store().load(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    alerts = generate_alerts(session)
    severity_counts: dict = {}
    for alert in alerts:
        sev = alert.get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return jsonify({
        "session_id": session_id,
        "total_alerts": len(alerts),
        "by_severity": severity_counts,
        "has_warnings": severity_counts.get("warning", 0) > 0,
    })


def init_alerts(app):
    app.register_blueprint(alerts_bp)
