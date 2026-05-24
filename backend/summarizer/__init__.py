"""Summarizer package — exposes all summarizer helpers for easy import."""

from backend.summarizer.summarize import summarize_session
from backend.summarizer.tags import classify_domain, compute_tags
from backend.summarizer.insights import generate_insights
from backend.summarizer.timeline import build_timeline
from backend.summarizer.goals import evaluate_goals
from backend.summarizer.heatmap import build_heatmap, peak_slot
from backend.summarizer.export import export_json, export_csv, export_markdown
from backend.summarizer.comparison import compare_sessions
from backend.summarizer.streak import compute_streak
from backend.summarizer.recommendations import generate_recommendations
from backend.summarizer.focus import compute_focus
from backend.summarizer.alerts import generate_alerts
from backend.summarizer.domains import compute_domain_frequency, top_domains
from backend.summarizer.patterns import detect_patterns
from backend.summarizer.productivity import compute_productivity
from backend.summarizer.replay import build_replay
from backend.summarizer.categories import compute_category_time, top_categories
from backend.summarizer.bookmarks import detect_bookmarks
from backend.summarizer.search import search_events, search_sessions
from backend.summarizer.notes import create_note, list_notes, summarize_notes
from backend.summarizer.digest import build_daily_digest
from backend.summarizer.wordcloud import build_wordcloud

__all__ = [
    "summarize_session",
    "classify_domain", "compute_tags",
    "generate_insights",
    "build_timeline",
    "evaluate_goals",
    "build_heatmap", "peak_slot",
    "export_json", "export_csv", "export_markdown",
    "compare_sessions",
    "compute_streak",
    "generate_recommendations",
    "compute_focus",
    "generate_alerts",
    "compute_domain_frequency", "top_domains",
    "detect_patterns",
    "compute_productivity",
    "build_replay",
    "compute_category_time", "top_categories",
    "detect_bookmarks",
    "search_events", "search_sessions",
    "create_note", "list_notes", "summarize_notes",
    "build_daily_digest",
    "build_wordcloud",
]
