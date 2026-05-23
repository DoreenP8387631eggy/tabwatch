"""Unit tests for backend/summarizer/notes.py"""

import pytest
from backend.summarizer.notes import create_note, list_notes, summarize_notes


def test_create_note_basic():
    note = create_note("sess-1", "Great focus session today")
    assert note["session_id"] == "sess-1"
    assert note["text"] == "Great focus session today"
    assert note["author"] == "user"
    assert "created_at" in note


def test_create_note_custom_author():
    note = create_note("sess-2", "Lots of distractions", author="alice")
    assert note["author"] == "alice"


def test_create_note_strips_whitespace():
    note = create_note("sess-3", "  trimmed  ")
    assert note["text"] == "trimmed"


def test_create_note_empty_raises():
    with pytest.raises(ValueError):
        create_note("sess-4", "")


def test_create_note_whitespace_only_raises():
    with pytest.raises(ValueError):
        create_note("sess-5", "   ")


def test_list_notes_no_filter():
    notes = [
        {"session_id": "a", "text": "x"},
        {"session_id": "b", "text": "y"},
    ]
    assert len(list_notes(notes)) == 2


def test_list_notes_filtered():
    notes = [
        {"session_id": "a", "text": "x"},
        {"session_id": "b", "text": "y"},
    ]
    result = list_notes(notes, session_id="a")
    assert len(result) == 1
    assert result[0]["session_id"] == "a"


def test_summarize_notes_empty():
    summary = summarize_notes([])
    assert summary["count"] == 0
    assert summary["latest"] is None
    assert summary["snippet"] is None


def test_summarize_notes_single():
    notes = [{"session_id": "s", "text": "Hello", "created_at": "2024-01-01T10:00:00+00:00"}]
    summary = summarize_notes(notes)
    assert summary["count"] == 1
    assert summary["snippet"] == "Hello"


def test_summarize_notes_long_text_truncated():
    long_text = "A" * 100
    notes = [{"session_id": "s", "text": long_text, "created_at": "2024-01-01T10:00:00+00:00"}]
    summary = summarize_notes(notes)
    assert summary["snippet"].endswith("...")
    assert len(summary["snippet"]) == 83
