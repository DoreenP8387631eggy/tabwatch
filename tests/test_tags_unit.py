"""Unit tests for tag classification logic in backend/summarizer/tags.py."""

import pytest
from backend.summarizer.tags import classify_domain, compute_tags


def test_classify_known_domain():
    assert classify_domain("github.com") == "coding"
    assert classify_domain("stackoverflow.com") == "coding"
    assert classify_domain("youtube.com") == "entertainment"
    assert classify_domain("reddit.com") == "social"
    assert classify_domain("mail.google.com") == "email"
    assert classify_domain("notion.so") == "productivity"


def test_classify_subdomain():
    assert classify_domain("www.github.com") == "coding"
    assert classify_domain("blog.medium.com") == "reading"


def test_classify_unknown_domain():
    assert classify_domain("unknownsite.xyz") == "other"
    assert classify_domain("mycompany.internal") == "other"


def test_compute_tags_single_category():
    domains = ["github.com", "github.com", "stackoverflow.com"]
    tags = compute_tags(domains)
    assert tags[0] == "coding"
    assert "other" not in tags


def test_compute_tags_excludes_other_when_mixed():
    domains = ["github.com", "github.com", "unknownsite.xyz"]
    tags = compute_tags(domains)
    assert "coding" in tags
    assert "other" not in tags


def test_compute_tags_only_unknown():
    domains = ["weird1.xyz", "weird2.abc"]
    tags = compute_tags(domains)
    assert tags == ["other"]


def test_compute_tags_empty():
    tags = compute_tags([])
    assert tags == []


def test_compute_tags_order_by_frequency():
    domains = [
        "youtube.com", "youtube.com", "youtube.com",
        "github.com", "github.com",
        "reddit.com",
    ]
    tags = compute_tags(domains)
    assert tags[0] == "entertainment"
    assert tags[1] == "coding"
    assert tags[2] == "social"
