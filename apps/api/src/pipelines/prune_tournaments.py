"""Pipeline to prune tournaments before a cutoff date."""

import logging
from datetime import date

from pydantic import BaseModel
from sqlalchemy import delete, func, select

from src.db.database import async_session_factory
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement

logger = logging.getLogger(__name__)


class PruneTournamentsResult(BaseModel):
    tournaments_deleted: int
    placements_deleted: int
    tournaments_remaining: int
    errors: list[str]
    success: bool


async def prune_tournaments(
    *,
    before_date: date,
    region: str | None = None,
    dry_run: bool = False,
) -> PruneTournamentsResult:
    """Delete tournaments (and their placements) before a cutoff date."""
    errors: list[str] = []

    async with async_session_factory() as session:
        try:
            # Build filter
            filters = [Tournament.date < before_date]
            if region:
                filters.append(Tournament.region == region)

            # Count what we'll delete
            count_q = select(func.count()).select_from(Tournament).where(*filters)
            result = await session.execute(count_q)
            tournaments_to_delete = result.scalar() or 0

            # Count placements that will cascade
            placement_count_q = (
                select(func.count())
                .select_from(TournamentPlacement)
                .join(Tournament)
                .where(*filters)
            )
            result = await session.execute(placement_count_q)
            placements_to_delete = result.scalar() or 0

            logger.info(
                "Pruning %d tournaments (%d placements) before %s%s",
                tournaments_to_delete,
                placements_to_delete,
                before_date,
                f" region={region}" if region else "",
            )

            if dry_run:
                remaining_q = select(func.count()).select_from(Tournament)
                if region:
                    remaining_q = remaining_q.where(Tournament.region == region)
                result = await session.execute(remaining_q)
                total = result.scalar() or 0
                remaining = total - tournaments_to_delete

                return PruneTournamentsResult(
                    tournaments_deleted=0,
                    placements_deleted=0,
                    tournaments_remaining=remaining,
                    errors=[],
                    success=True,
                )

            # Delete placements first (explicit, avoids relying on CASCADE)
            del_placements = delete(TournamentPlacement).where(
                TournamentPlacement.tournament_id.in_(
                    select(Tournament.id).where(*filters)
                )
            )
            await session.execute(del_placements)
            placements_deleted = placements_to_delete

            # Delete tournaments
            del_tournaments = delete(Tournament).where(*filters)
            await session.execute(del_tournaments)
            tournaments_deleted = tournaments_to_delete

            await session.commit()

            # Count remaining
            remaining_q = select(func.count()).select_from(Tournament)
            if region:
                remaining_q = remaining_q.where(Tournament.region == region)
            result = await session.execute(remaining_q)
            remaining = result.scalar() or 0

            logger.info(
                "Pruned %d tournaments (%d placements), %d remaining",
                tournaments_deleted,
                placements_deleted,
                remaining,
            )

            return PruneTournamentsResult(
                tournaments_deleted=tournaments_deleted,
                placements_deleted=placements_deleted,
                tournaments_remaining=remaining,
                errors=[],
                success=True,
            )

        except Exception as e:
            await session.rollback()
            msg = f"Prune failed: {e}"
            logger.exception(msg)
            errors.append(msg)
            return PruneTournamentsResult(
                tournaments_deleted=0,
                placements_deleted=0,
                tournaments_remaining=0,
                errors=errors,
                success=False,
            )
