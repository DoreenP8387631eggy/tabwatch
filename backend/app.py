"""Flask application factory."""

from flask import Flask, jsonify
from backend.storage.session_store import SessionStore
from backend.api.sessions import sessions_bp
from backend.api.summary import summary_bp
from backend.api.tags import tags_bp
from backend.api.insights import insights_bp
from backend.api.timeline import timeline_bp
from backend.api.goals import goals_bp


def create_app(store: SessionStore | None = None) -> Flask:
    app = Flask(__name__)

    if store is None:
        store = SessionStore()
    app.config["store"] = store

    app.register_blueprint(sessions_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(goals_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
