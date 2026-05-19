"""Heatmap builder: aggregates activity by day-of-week and hour-of-day."""

from collections import defaultdict
from typing import Dict, List

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def build_heatmap(session) -> Dict:
    """
    Return a heatmap dict keyed by (day_label, hour) with visit counts.

    Output structure:
    {
        "days": ["Mon", ..., "Sun"],
        "hours": [0, 1, ..., 23],
        "cells": [
            {"day": "Mon", "hour": 9, "count": 4},
            ...
        ],
        "max_count": 7
    }
    """
    counts: Dict[tuple, int] = defaultdict(int)

    for event in session.events:
        ts = event.timestamp
        day_label = DAYS[ts.weekday()]
        hour = ts.hour
        counts[(day_label, hour)] += 1

    cells: List[Dict] = [
        {"day": day, "hour": hour, "count": count}
        for (day, hour), count in counts.items()
    ]
    cells.sort(key=lambda c: (DAYS.index(c["day"]), c["hour"]))

    max_count = max((c["count"] for c in cells), default=0)

    return {
        "days": DAYS,
        "hours": list(range(24)),
        "cells": cells,
        "max_count": max_count,
    }


def peak_slot(heatmap: Dict) -> Dict:
    """Return the single cell with the highest activity count."""
    cells = heatmap.get("cells", [])
    if not cells:
        return {}
    return max(cells, key=lambda c: c["count"])
