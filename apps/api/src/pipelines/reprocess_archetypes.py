"""Reprocess archetype labels for existing tournament placements."""

import logging
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from src.db.database import async_session_factory
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.services.archetype_normalizer import ArchetypeNormalizer

logger = logging.getLogger(__name__)


@dataclass
class ReprocessArchetypesResult:
    """Result of reprocess_archetypes pipeline."""

    processed: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    next_cursor: str | None = None
    total_remaining: int = 0

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def reprocess_archetypes(
    region: str = "JP",
    batch_size: int = 200,
    cursor: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> ReprocessArchetypesResult:
    """Reprocess archetype labels for existing placements.

    Queries placements joined with tournaments, resolves each through
    ArchetypeNormalizer, and updates the archetype + detection_method.

    For placements WITH raw_archetype_sprites: resolves from stored
    sprites. For placements WITHOUT sprites: skips (no sprite data to
    work with).

    Args:
        region: Tournament region to reprocess (default "JP").
        batch_size: Number of placements per batch.
        cursor: Opaque pagination cursor (placement UUID string).
        force: If True, re-run even if detection_method is populated.
        dry_run: If True, log changes without writing to DB.

    Returns:
        ReprocessArchetypesResult with counts and next_cursor.
    """
    result = ReprocessArchetypesResult()

    async with async_session_factory() as session:
        # Load normalizer with DB sprites
        normalizer = ArchetypeNormalizer()
        await normalizer.load_db_sprites(session)

        # Build query for placements to process
        query = (
            select(TournamentPlacement)
            .join(Tournament)
            .where(Tournament.region == region)
        )

        if not force:
            query = query.where(
                TournamentPlacement.archetype_detection_method.is_(None)
            )

        if cursor:
            query = query.where(TournamentPlacement.id > cursor)

        query = query.order_by(TournamentPlacement.id).limit(batch_size)

        try:
            rows = await session.execute(query)
            placements = rows.scalars().all()
        except SQLAlchemyError as e:
            result.errors.append(f"Query failed: {e}")
            return result

        # Count remaining
        count_query = (
            select(func.count())
            .select_from(TournamentPlacement)
            .join(Tournament)
            .where(Tournament.region == region)
        )
        if not force:
            count_query = count_query.where(
                TournamentPlacement.archetype_detection_method.is_(None)
            )
        if cursor:
            count_query = count_query.where(TournamentPlacement.id > cursor)

        try:
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
        except SQLAlchemyError:
            total = 0

        last_id = None

        for placement in placements:
            result.processed += 1
            last_id = str(placement.id)

            sprite_urls = placement.raw_archetype_sprites or []

            if not sprite_urls:
                result.skipped += 1
                continue

            html_archetype = placement.raw_archetype or placement.archetype

            new_archetype, raw, method = normalizer.resolve(
                sprite_urls,
                html_archetype,
                placement.decklist,
            )

            if (
                new_archetype != placement.archetype
                or placement.archetype_detection_method != method
            ):
                if not dry_run:
                    placement.archetype = new_archetype
                    placement.archetype_detection_method = method
                result.updated += 1
                logger.info(
                    "reprocess_updated",
                    extra={
                        "placement_id": str(placement.id),
                        "old_archetype": (
                            placement.archetype if dry_run else new_archetype
                        ),
                        "new_archetype": new_archetype,
                        "method": method,
                        "dry_run": dry_run,
                    },
                )
            else:
                result.skipped += 1

        if not dry_run:
            try:
                await session.commit()
            except SQLAlchemyError as e:
                result.errors.append(f"Commit failed: {e}")
                return result

        # Set pagination cursor
        remaining = total - len(placements)
        if remaining > 0 and last_id:
            result.next_cursor = last_id
            result.total_remaining = remaining

    return result
