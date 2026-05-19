"""Tag classification for browsing sessions based on visited domains."""

from collections import Counter
from typing import List, Dict

# Domain-to-category mapping
DOMAIN_TAGS: Dict[str, str] = {
    "github.com": "coding",
    "stackoverflow.com": "coding",
    "docs.python.org": "coding",
    "developer.mozilla.org": "coding",
    "gitlab.com": "coding",
    "youtube.com": "entertainment",
    "netflix.com": "entertainment",
    "twitch.tv": "entertainment",
    "reddit.com": "social",
    "twitter.com": "social",
    "x.com": "social",
    "linkedin.com": "social",
    "facebook.com": "social",
    "news.ycombinator.com": "news",
    "bbc.com": "news",
    "cnn.com": "news",
    "medium.com": "reading",
    "substack.com": "reading",
    "notion.so": "productivity",
    "trello.com": "productivity",
    "jira.atlassian.com": "productivity",
    "docs.google.com": "productivity",
    "mail.google.com": "email",
    "outlook.com": "email",
}


def classify_domain(domain: str) -> str:
    """Return a category tag for a given domain, or 'other' if unknown."""
    for known_domain, tag in DOMAIN_TAGS.items():
        if domain.endswith(known_domain):
            return tag
    return "other"


def compute_tags(domains: List[str]) -> List[str]:
    """Return a ranked list of tags based on domain visit frequency."""
    tag_counts: Counter = Counter()
    for domain in domains:
        tag = classify_domain(domain)
        tag_counts[tag] += 1

    # Return tags sorted by frequency, excluding 'other' if other tags exist
    sorted_tags = [tag for tag, _ in tag_counts.most_common()]
    if len(sorted_tags) > 1 and "other" in sorted_tags:
        sorted_tags.remove("other")
    return sorted_tags
