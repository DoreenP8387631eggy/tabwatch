from datetime import date, timedelta
from typing import List
from backend.models.session import BrowsingSession


def _session_date(session: BrowsingSession) -> date:
    """Extract the calendar date from a session's start time."""
    return session.start_time.date()


def compute_streak(sessions: List[BrowsingSession]) -> dict:
    """
    Compute the current and longest streak of consecutive days
    with at least one closed browsing session.

    Returns a dict with:
      - current_streak: int
      - longest_streak: int
      - streak_start: str (ISO date) or None
      - today_covered: bool
    """
    closed = [s for s in sessions if s.end_time is not None]
    if not closed:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "streak_start": None,
            "today_covered": False,
        }

    unique_dates = sorted({_session_date(s) for s in closed})
    today = date.today()

    # Build runs of consecutive dates
    runs: List[List[date]] = []
    current_run: List[date] = [unique_dates[0]]
    for d in unique_dates[1:]:
        if d - current_run[-1] == timedelta(days=1):
            current_run.append(d)
        else:
            runs.append(current_run)
            current_run = [d]
    runs.append(current_run)

    longest_streak = max(len(r) for r in runs)

    # Current streak: the run that ends today or yesterday
    last_run = runs[-1]
    last_date = last_run[-1]
    if last_date >= today - timedelta(days=1):
        current_streak = len(last_run)
        streak_start = last_run[0].isoformat()
    else:
        current_streak = 0
        streak_start = None

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "streak_start": streak_start,
        "today_covered": last_date == today,
    }
