"""Focus score analysis: measures depth of engagement per domain visit."""

from collections import defaultdict
from typing import Dict, List

from backend.models.session import BrowsingSession

# Minimum seconds on a page to count as "focused"
FOCUS_THRESHOLD_SECONDS = 30
# A visit longer than this is considered deep focus
DEEP_FOCUS_SECONDS = 120


def compute_focus(session: BrowsingSession) -> Dict:
    """Return focus metrics for a browsing session."""
    events = session.events
    if not events:
        return {
            "focused_visits": 0,
            "shallow_visits": 0,
            "deep_focus_visits": 0,
            "focus_ratio": 0.0,
            "top_focus_domains": [],
        }

    domain_focus_time: Dict[str, float] = defaultdict(float)
    focused = 0
    shallow = 0
    deep_focus = 0

    for i, event in enumerate(events):
        # Estimate time on page: diff to next event or 0 for last
        if i + 1 < len(events):
            duration = (events[i + 1].timestamp - event.timestamp).total_seconds()
        else:
            duration = 0.0

        duration = max(0.0, duration)
        domain = _extract_domain(event.url)

        if duration >= FOCUS_THRESHOLD_SECONDS:
            focused += 1
            domain_focus_time[domain] += duration
            if duration >= DEEP_FOCUS_SECONDS:
                deep_focus += 1
        else:
            shallow += 1

    total = focused + shallow
    focus_ratio = round(focused / total, 3) if total > 0 else 0.0

    top_domains: List[Dict] = sorted(
        [{"domain": d, "focus_seconds": round(s, 1)} for d, s in domain_focus_time.items()],
        key=lambda x: x["focus_seconds"],
        reverse=True,
    )[:5]

    return {
        "focused_visits": focused,
        "shallow_visits": shallow,
        "deep_focus_visits": deep_focus,
        "focus_ratio": focus_ratio,
        "top_focus_domains": top_domains,
    }


def _extract_domain(url: str) -> str:
    """Extract bare domain from a URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.netloc or url
        return host.replace("www.", "")
    except Exception:
        return url
