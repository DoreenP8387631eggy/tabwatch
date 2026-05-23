"""Export browsing session data to various formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from backend.models.session import BrowsingSession
from backend.summarizer.summarize import summarize_session
from backend.summarizer.tags import compute_tags


def export_json(session: BrowsingSession) -> str:
    """Return a JSON string with full session data and summary."""
    summary = summarize_session(session)
    tags = compute_tags(session)
    payload: dict[str, Any] = {
        "session_id": session.session_id,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "summary": summary,
        "tags": tags,
        "events": [e.__dict__ for e in session.events],
    }
    return json.dumps(payload, indent=2, default=str)


def export_csv(session: BrowsingSession) -> str:
    """Return a CSV string with one row per tab event."""
    output = io.StringIO()
    fieldnames = ["timestamp", "url", "title", "duration_seconds", "event_type"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for event in session.events:
        writer.writerow(
            {
                "timestamp": event.timestamp,
                "url": event.url,
                "title": getattr(event, "title", ""),
                "duration_seconds": getattr(event, "duration_seconds", ""),
                "event_type": getattr(event, "event_type", ""),
            }
        )
    return output.getvalue()


def export_markdown(session: BrowsingSession) -> str:
    """Return a Markdown report for the session."""
    summary = summarize_session(session)
    tags = compute_tags(session)
    lines = [
        f"# Browsing Session Report",
        f"",
        f"**Session ID:** `{session.session_id}`  ",
        f"**Start:** {session.start_time}  ",
        f"**End:** {session.end_time or 'In progress'}  ",
        f"",
        f"## Summary",
        f"",
        f"- Total events: {summary.get('total_events', 0)}",
        f"- Unique domains: {summary.get('unique_domains', 0)}",
        f"- Total duration: {summary.get('total_duration_seconds', 0)}s",
        f"",
        f"## Tags",
        f"",
    ]
    for tag, count in (tags or {}).items():
        lines.append(f"- **{tag}**: {count} visit(s)")
    lines += [
        f"",
        f"## Top Domains",
        f"",
    ]
    for domain, count in (summary.get("top_domains") or {}).items():
        lines.append(f"- `{domain}`: {count} visit(s)")
    return "\n".join(lines) + "\n"
