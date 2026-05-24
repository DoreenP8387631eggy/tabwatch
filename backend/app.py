"""Application factory for TabWatch backend."""

from flask import Flask, jsonify
from backend.storage.session_store import SessionStore
from backend.api.sessions import sessions_bp
from backend.api.summary import summary_bp
from backend.api.tags import tags_bp
from backend.api.insights import init_insights
from backend.api.timeline import init_timeline
from backend.api.goals import init_goals
from backend.api.heatmap import init_heatmap
from backend.api.export import init_export
from backend.api.comparison import init_comparison
from backend.api.streak import init_streak
from backend.api.focus import init_focus
from backend.api.alerts import init_alerts
from backend.api.patterns import init_patterns
from backend.api.productivity import init_productivity
from backend.api.replay import init_replay
from backend.api.categories import init_categories
from backend.api.bookmarks import init_bookmarks
from backend.api.search import init_search
from backend.api.notes import init_notes
from backend.api.digest import init_digest
from backend.api.wordcloud import init_wordcloud
from backend.api.milestones import init_milestones
from backend.api.badges import init_badges
from backend.api.velocity import init_velocity
from backend.api.mood import init_mood
from backend.api.rhythm import init_rhythm


def create_app(store: SessionStore | None = None) -> Flask:
    app = Flask(__name__)

    if store is None:
        store = SessionStore()

    app.register_blueprint(sessions_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(init_insights(store))
    app.register_blueprint(init_timeline(store))
    app.register_blueprint(init_goals(store))
    app.register_blueprint(init_heatmap(store))
    app.register_blueprint(init_export(store))
    app.register_blueprint(init_comparison(store))
    app.register_blueprint(init_streak(store))
    app.register_blueprint(init_focus(store))
    app.register_blueprint(init_alerts(store))
    app.register_blueprint(init_patterns(store))
    app.register_blueprint(init_productivity(store))
    app.register_blueprint(init_replay(store))
    app.register_blueprint(init_categories(store))
    app.register_blueprint(init_bookmarks(store))
    app.register_blueprint(init_search(store))
    app.register_blueprint(init_notes(store))
    app.register_blueprint(init_digest(store))
    app.register_blueprint(init_wordcloud(store))
    app.register_blueprint(init_milestones(store))
    app.register_blueprint(init_badges(store))
    app.register_blueprint(init_velocity(store))
    app.register_blueprint(init_mood(store))
    app.register_blueprint(init_rhythm(store))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
