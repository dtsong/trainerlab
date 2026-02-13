"""Backfill major format window metadata on tournaments."""

import logging
from dataclasses import dataclass, field

from sqlalchemy import select

from src.db.database import async_session_factory
from src.models import MajorFormatWindow, Tournament
from src.services.major_format_windows import (
    is_official_major_tier,
    resolve_major_window_for_date,
    validate_major_window_sequence,
)

logger = logging.getLogger(__name__)


@dataclass
class BackfillMajorFormatWindowsResult:
    """Result of major format window backfill."""

    tournaments_scanned: int = 0
    tournaments_updated: int = 0
    tournaments_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def backfill_major_format_windows(
    *,
    dry_run: bool = False,
) -> BackfillMajorFormatWindowsResult:
    """Backfill date-based major format labels for official major tournaments."""

    result = BackfillMajorFormatWindowsResult()

    async with async_session_factory() as session:
        windows_result = await session.execute(
            select(MajorFormatWindow).where(MajorFormatWindow.is_active.is_(True))
        )
        windows = windows_result.scalars().all()
        window_warnings = validate_major_window_sequence(windows)
        if window_warnings:
            result.errors.extend(window_warnings)
            for warning in window_warnings:
                logger.warning("Major format window validation warning: %s", warning)

        tournaments_result = await session.execute(select(Tournament))
        tournaments = tournaments_result.scalars().all()

        for tournament in tournaments:
            result.tournaments_scanned += 1

            new_key: str | None = None
            new_label: str | None = None
            if is_official_major_tier(tournament.tier):
                window = resolve_major_window_for_date(windows, tournament.date)
                if window is not None:
                    new_key = window.key
                    new_label = window.display_name

            if (
                tournament.major_format_key == new_key
                and tournament.major_format_label == new_label
            ):
                result.tournaments_skipped += 1
                continue

            tournament.major_format_key = new_key
            tournament.major_format_label = new_label
            result.tournaments_updated += 1

        if dry_run:
            await session.rollback()
        else:
            await session.commit()

    return result
