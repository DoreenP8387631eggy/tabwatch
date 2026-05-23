"""Unit tests for the export module."""

import json

import pytest

from backend.models.session import BrowsingSession, TabEvent
from backend.summarizer.export import export_csv, export_json, export_markdown


def _make_session() -> BrowsingSession:
    s = BrowsingSession(session_id="unit-export-1", label="unit")
    for url, title in [
        ("https://github.com/org/project", "GitHub"),
        ("https://stackoverflow.com/questions/1", "Stack Overflow"),
    ]:
        s.add_event(
            TabEvent(
                url=url,
                title=title,
                timestamp="2024-01-01T10:00:00",
                duration_seconds=90,
                event_type="visit",
            )
        )
    s.close()
    return s


def test_export_json_structure():
    s = _make_session()
    result = export_json(s)
    data = json.loads(result)
    assert data["session_id"] == "unit-export-1"
    assert "summary" in data
    assert "tags" in data
    assert "events" in data
    assert len(data["events"]) == 2


def test_export_csv_rows():
    s = _make_session()
    result = export_csv(s)
    lines = [l for l in result.splitlines() if l.strip()]
    assert lines[0] == "timestamp,url,title,duration_seconds,event_type"
    assert len(lines) == 3  # header + 2 events
    assert "github.com" in result
    assert "stackoverflow.com" in result


def test_export_markdown_sections():
    s = _make_session()
    result = export_markdown(s)
    assert "# Browsing Session Report" in result
    assert "unit-export-1" in result
    assert "## Summary" in result
    assert "## Tags" in result
    assert "## Top Domains" in result


def test_export_json_empty_session():
    s = BrowsingSession(session_id="empty-export", label="empty")
    s.close()
    result = export_json(s)
    data = json.loads(result)
    assert data["events"] == []
    assert data["summary"]["total_events"] == 0


def test_export_csv_empty_session():
    s = BrowsingSession(session_id="empty-csv", label="empty")
    s.close()
    result = export_csv(s)
    lines = [l for l in result.splitlines() if l.strip()]
    assert len(lines) == 1  # header only
