"""Utilities for official major format windows."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.major_format_window import MajorFormatWindow

OFFICIAL_MAJOR_TIERS = {
    "major",
    "regional",
    "international",
    "worlds",
    "special",
}


def is_official_major_tier(tier: str | None) -> bool:
    """Return True when a tournament tier is an official major tier."""

    return tier in OFFICIAL_MAJOR_TIERS


def validate_major_window_sequence(
    windows: Sequence[MajorFormatWindow],
) -> list[str]:
    """Validate a contiguous, non-overlapping major window sequence.

    Validation rules:
    - ``start_date`` must be in ascending order.
    - Adjacent windows cannot overlap.
    - Adjacent windows should be contiguous (no day gaps).
    - Open-ended windows (``end_date is None``) must be last.
    """

    if not windows:
        return []

    warnings: list[str] = []
    ordered = sorted(windows, key=lambda w: w.start_date)

    for idx, current in enumerate(ordered):
        if current.end_date is not None and current.end_date < current.start_date:
            warnings.append(
                f"Invalid window '{current.key}': end_date before start_date"
            )

        if current.end_date is None and idx != len(ordered) - 1:
            warnings.append(
                f"Invalid window '{current.key}': open-ended window must be last"
            )

        if idx == 0:
            continue

        prev = ordered[idx - 1]
        if prev.end_date is None:
            warnings.append(
                f"Invalid sequence: '{prev.key}' is open-ended before '{current.key}'"
            )
            continue

        if prev.end_date >= current.start_date:
            warnings.append(
                f"Overlap detected: '{prev.key}' and '{current.key}' overlap"
            )
            continue

        expected_next_start = date.fromordinal(prev.end_date.toordinal() + 1)
        if current.start_date != expected_next_start:
            warnings.append(f"Gap detected between '{prev.key}' and '{current.key}'")

    return warnings


def resolve_major_window_for_date(
    windows: Sequence[MajorFormatWindow],
    target_date: date,
) -> MajorFormatWindow | None:
    """Resolve the major format window containing the target date."""

    for window in sorted(windows, key=lambda w: w.start_date):
        if target_date < window.start_date:
            continue
        if window.end_date is None or target_date <= window.end_date:
            return window
    return None


async def get_major_window_for_date(
    session: AsyncSession,
    target_date: date,
) -> MajorFormatWindow | None:
    """Fetch the major format window covering ``target_date`` from DB."""

    result = await session.execute(
        select(MajorFormatWindow).where(MajorFormatWindow.is_active.is_(True))
    )
    windows = result.scalars().all()
    return resolve_major_window_for_date(windows, target_date)
