"""Shared date utilities."""

from datetime import date


def days_until(event_date: date) -> int | None:
    """Compute days until an event, or None if past."""
    delta = (event_date - date.today()).days
    return delta if delta >= 0 else None
