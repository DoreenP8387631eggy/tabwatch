"""Streak analysis: compute daily usage streaks from session metadata."""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from backend.models.session import BrowsingSession


def _session_date(session: BrowsingSession) -> str:
    """Return ISO date string (YYYY-MM-DD) for the session start time."""
    dt = datetime.fromtimestamp(session.start_time, tz=timezone.utc)
    return dt.date().isoformat()


def compute_streak(sessions: List[BrowsingSession]) -> Dict[str, Any]:
    """
    Given a list of BrowsingSession objects, compute:
      - current_streak: consecutive days ending on the most recent session date
      - longest_streak: longest run of consecutive days ever seen
      - active_days: sorted list of unique dates with at least one session
      - total_sessions: total number of sessions provided
    """
    if not sessions:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "active_days": [],
            "total_sessions": 0,
        }

    # Collect unique active dates
    active_dates = sorted(
        set(_session_date(s) for s in sessions)
    )

    # Convert to date objects for arithmetic
    from datetime import date
    date_objs = [date.fromisoformat(d) for d in active_dates]

    # Compute longest streak
    longest = 1
    current_run = 1
    for i in range(1, len(date_objs)):
        if (date_objs[i] - date_objs[i - 1]).days == 1:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1

    # Compute current streak (streak ending on the last active day)
    today = datetime.now(tz=timezone.utc).date()
    last_day = date_objs[-1]

    # Streak is only "current" if last active day is today or yesterday
    if (today - last_day).days > 1:
        current_streak = 0
    else:
        current_streak = 1
        for i in range(len(date_objs) - 1, 0, -1):
            if (date_objs[i] - date_objs[i - 1]).days == 1:
                current_streak += 1
            else:
                break

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "active_days": active_dates,
        "total_sessions": len(sessions),
    }
