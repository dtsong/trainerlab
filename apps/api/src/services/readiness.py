"""Operational readiness evaluation helpers."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta

logger = logging.getLogger(__name__)


def next_tuesday_utc(event_end: date) -> date:
    """Return the next Tuesday (UTC date) on or after event_end."""
    tuesday = 1  # Monday=0, Tuesday=1
    delta = (tuesday - event_end.weekday()) % 7
    return event_end + timedelta(days=delta)


def evaluate_tpci_post_major_readiness(
    *,
    latest_major_end_date: date | None,
    snapshot_date: date | None,
    sample_size: int | None,
    now_utc: datetime | None = None,
) -> dict:
    """Compute readiness state for fast-follow operations.

    Policy:
    - By Tuesday UTC after the major ends, we expect at least partial official data.
    - After Tuesday UTC passes, we expect fresh official data (>=64 placements).
    """
    now = now_utc or datetime.now(UTC)
    today = now.date()

    size = sample_size or 0
    meets_partial = size >= 8
    meets_fresh = size >= 64

    # Default evaluation with no event context
    if not latest_major_end_date:
        if meets_fresh:
            return {
                "status": "pass",
                "message": (
                    "No major event context; official snapshot sample is healthy."
                ),
                "deadline_date": None,
                "deadline_missed": False,
                "meets_partial": meets_partial,
                "meets_fresh": meets_fresh,
            }
        return {
            "status": "fail",
            "message": "No major event context and official snapshot sample is low.",
            "deadline_date": None,
            "deadline_missed": False,
            "meets_partial": meets_partial,
            "meets_fresh": meets_fresh,
        }

    deadline_date: date = next_tuesday_utc(latest_major_end_date)

    # Ensure the snapshot reflects post-major data; otherwise treat as not ready.
    if snapshot_date is not None and snapshot_date < latest_major_end_date:
        return {
            "status": "fail",
            "message": "Official snapshot is older than the latest major end date.",
            "deadline_date": deadline_date,
            "deadline_missed": today > deadline_date,
            "meets_partial": False,
            "meets_fresh": False,
        }

    # With major event context
    if today <= deadline_date:
        if meets_partial:
            return {
                "status": "pass",
                "message": (
                    "Post-major tracking is on schedule (partial data available)."
                ),
                "deadline_date": deadline_date,
                "deadline_missed": False,
                "meets_partial": meets_partial,
                "meets_fresh": meets_fresh,
            }
        return {
            "status": "fail",
            "message": (
                "Post-major data not yet available; expected partial by Tuesday UTC."
            ),
            "deadline_date": deadline_date,
            "deadline_missed": False,
            "meets_partial": meets_partial,
            "meets_fresh": meets_fresh,
        }

    # After Tuesday deadline
    if meets_fresh:
        return {
            "status": "pass",
            "message": "Post-major snapshot meets freshness target.",
            "deadline_date": deadline_date,
            "deadline_missed": False,
            "meets_partial": meets_partial,
            "meets_fresh": meets_fresh,
        }

    return {
        "status": "fail",
        "message": (
            "Major-event update expected by Tuesday UTC; freshness target not met."
        ),
        "deadline_date": deadline_date,
        "deadline_missed": True,
        "meets_partial": meets_partial,
        "meets_fresh": meets_fresh,
    }
