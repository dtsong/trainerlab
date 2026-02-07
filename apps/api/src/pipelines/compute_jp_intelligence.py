"""JP intelligence pipeline.

Derives JP-specific intelligence data from existing snapshots and
adoption rate data:
- New archetypes: JP-only archetypes not present in global meta
- Card innovations: Cards with significant JP competitive adoption
"""

import logging
import re
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory
from src.models.card import Card
from src.models.jp_card_adoption_rate import JPCardAdoptionRate
from src.models.jp_card_innovation import JPCardInnovation
from src.models.jp_new_archetype import JPNewArchetype
from src.models.meta_snapshot import MetaSnapshot

logger = logging.getLogger(__name__)

# Thresholds
JP_ARCHETYPE_MIN_SHARE = 0.01  # 1% share to be considered
GLOBAL_ARCHETYPE_MAX_SHARE = 0.005  # <0.5% in global = JP-only
JP_ARCHETYPE_DROP_THRESHOLD = 0.005  # Remove if below 0.5%
INNOVATION_MIN_INCLUSION = 0.05  # 5% inclusion to qualify
INNOVATION_DROP_THRESHOLD = 0.02  # Remove if below 2%


def _slugify(name: str) -> str:
    """Convert archetype name to slug ID."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _impact_rating(inclusion_rate: float) -> int:
    """Compute competitive impact rating (1-5) from inclusion rate."""
    if inclusion_rate > 0.30:
        return 5
    if inclusion_rate > 0.20:
        return 4
    if inclusion_rate > 0.10:
        return 3
    if inclusion_rate > 0.05:
        return 2
    return 1


@dataclass
class ComputeJPIntelligenceResult:
    """Result of JP intelligence computation."""

    new_archetypes_found: int = 0
    new_archetypes_removed: int = 0
    innovations_found: int = 0
    innovations_removed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def compute_new_archetypes(
    session: AsyncSession,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Identify JP-only archetypes not present in global meta.

    Returns:
        Tuple of (found_count, removed_count).
    """
    # Get latest JP (BO1, standard) snapshot
    jp_snap = await session.execute(
        select(MetaSnapshot)
        .where(
            MetaSnapshot.region == "JP",
            MetaSnapshot.format == "standard",
            MetaSnapshot.best_of == 1,
        )
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(1)
    )
    jp_snapshot = jp_snap.scalar_one_or_none()

    # Get latest Global (BO3, standard) snapshot
    global_snap = await session.execute(
        select(MetaSnapshot)
        .where(
            MetaSnapshot.region.is_(None),
            MetaSnapshot.format == "standard",
            MetaSnapshot.best_of == 3,
        )
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(1)
    )
    global_snapshot = global_snap.scalar_one_or_none()

    if not jp_snapshot or not global_snapshot:
        logger.warning(
            "Missing snapshots for JP archetype computation: jp=%s, global=%s",
            jp_snapshot is not None,
            global_snapshot is not None,
        )
        return 0, 0

    jp_shares = jp_snapshot.archetype_shares or {}
    global_shares = global_snapshot.archetype_shares or {}
    jp_trends = jp_snapshot.trends or {}

    found = 0
    for name, jp_share in jp_shares.items():
        global_share = global_shares.get(name, 0.0)
        if (
            jp_share >= JP_ARCHETYPE_MIN_SHARE
            and global_share < GLOBAL_ARCHETYPE_MAX_SHARE
        ):
            archetype_id = _slugify(name)
            trend_data = jp_trends.get(name, {})
            trend_dir = (
                trend_data.get("direction") if isinstance(trend_data, dict) else None
            )

            if not dry_run:
                stmt = pg_insert(JPNewArchetype).values(
                    id=uuid4(),
                    archetype_id=archetype_id,
                    name=name,
                    jp_meta_share=jp_share,
                    jp_trend=trend_dir,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["archetype_id"],
                    set_={
                        "jp_meta_share": jp_share,
                        "jp_trend": trend_dir,
                        "name": name,
                    },
                )
                await session.execute(stmt)
            found += 1

    # Remove archetypes that dropped below threshold in JP
    removed = 0
    if not dry_run:
        existing = await session.execute(
            select(JPNewArchetype.archetype_id, JPNewArchetype.id)
        )
        for archetype_id, row_id in existing.all():
            # Find matching name in current JP shares
            matching_share = None
            for name, share in jp_shares.items():
                if _slugify(name) == archetype_id:
                    matching_share = share
                    break
            if matching_share is None or matching_share < JP_ARCHETYPE_DROP_THRESHOLD:
                await session.execute(
                    delete(JPNewArchetype).where(JPNewArchetype.id == row_id)
                )
                removed += 1

    if not dry_run:
        await session.flush()

    logger.info(
        "JP new archetypes: found=%d, removed=%d",
        found,
        removed,
    )
    return found, removed


async def compute_card_innovations(
    session: AsyncSession,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Derive card innovations from JP adoption rate data.

    Returns:
        Tuple of (found_count, removed_count).
    """
    # Get latest period's adoption rates
    max_period = await session.execute(select(func.max(JPCardAdoptionRate.period_end)))
    latest_period_end = max_period.scalar_one_or_none()

    if not latest_period_end:
        logger.warning("No JP adoption rate data available")
        return 0, 0

    rates_result = await session.execute(
        select(JPCardAdoptionRate).where(
            JPCardAdoptionRate.period_end == latest_period_end,
            JPCardAdoptionRate.inclusion_rate >= INNOVATION_MIN_INCLUSION,
        )
    )
    rates = rates_result.scalars().all()

    if not rates:
        logger.info(
            "No adoption rates above threshold for period ending %s",
            latest_period_end,
        )
        return 0, 0

    found = 0
    for rate in rates:
        # Try to match to a Card record
        card = None
        if rate.card_name_en:
            card_result = await session.execute(
                select(Card).where(Card.name == rate.card_name_en).limit(1)
            )
            card = card_result.scalar_one_or_none()

        if not card and rate.card_name_jp:
            card_result = await session.execute(
                select(Card).where(Card.japanese_name == rate.card_name_jp).limit(1)
            )
            card = card_result.scalar_one_or_none()

        card_id = card.id if card else rate.card_id
        card_name = rate.card_name_en or (card.name if card else rate.card_id)
        set_code = card.set_id if card else ""
        impact = _impact_rating(rate.inclusion_rate)

        archetypes = [rate.archetype_context] if rate.archetype_context else None

        if not dry_run:
            stmt = pg_insert(JPCardInnovation).values(
                id=uuid4(),
                card_id=card_id,
                card_name=card_name,
                card_name_jp=rate.card_name_jp,
                set_code=set_code,
                adoption_rate=rate.inclusion_rate,
                adoption_trend=None,
                archetypes_using=archetypes,
                competitive_impact_rating=impact,
                sample_size=rate.sample_size or 0,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["card_id"],
                set_={
                    "card_name": card_name,
                    "card_name_jp": rate.card_name_jp,
                    "set_code": set_code,
                    "adoption_rate": rate.inclusion_rate,
                    "archetypes_using": archetypes,
                    "competitive_impact_rating": impact,
                    "sample_size": rate.sample_size or 0,
                },
            )
            await session.execute(stmt)
        found += 1

    # Remove innovations where adoption dropped below threshold
    removed = 0
    if not dry_run:
        # Build a set of card_ids from current period that are above
        # the drop threshold
        current_ids_result = await session.execute(
            select(JPCardAdoptionRate.card_id).where(
                JPCardAdoptionRate.period_end == latest_period_end,
                JPCardAdoptionRate.inclusion_rate >= INNOVATION_DROP_THRESHOLD,
            )
        )
        current_card_ids = {row[0] for row in current_ids_result.all()}

        # Also map by card_name_en for cards matched to Card table
        current_names_result = await session.execute(
            select(JPCardAdoptionRate.card_name_en).where(
                JPCardAdoptionRate.period_end == latest_period_end,
                JPCardAdoptionRate.inclusion_rate >= INNOVATION_DROP_THRESHOLD,
                JPCardAdoptionRate.card_name_en.isnot(None),
            )
        )
        current_names = {row[0] for row in current_names_result.all()}

        existing_innovations = await session.execute(
            select(JPCardInnovation.id, JPCardInnovation.card_id)
        )
        for row_id, cid in existing_innovations.all():
            if cid not in current_card_ids and cid not in current_names:
                await session.execute(
                    delete(JPCardInnovation).where(JPCardInnovation.id == row_id)
                )
                removed += 1

    if not dry_run:
        await session.flush()

    logger.info(
        "JP card innovations: found=%d, removed=%d",
        found,
        removed,
    )
    return found, removed


async def compute_jp_intelligence(
    dry_run: bool = False,
) -> ComputeJPIntelligenceResult:
    """Orchestrate JP intelligence computation.

    Runs both new archetype detection and card innovation derivation.
    """
    result = ComputeJPIntelligenceResult()

    async with async_session_factory() as session:
        # Backfill empty sprite_urls on existing DB rows (idempotent)
        if not dry_run:
            try:
                from src.services.archetype_normalizer import (
                    ArchetypeNormalizer,
                )

                await ArchetypeNormalizer.backfill_sprite_urls(session)
            except Exception:
                logger.warning(
                    "Sprite URL backfill failed (non-fatal)",
                    exc_info=True,
                )

        try:
            found, removed = await compute_new_archetypes(session, dry_run=dry_run)
            result.new_archetypes_found = found
            result.new_archetypes_removed = removed
        except Exception as e:
            msg = f"Error computing new archetypes: {e}"
            logger.error(msg, exc_info=True)
            result.errors.append(msg)

        try:
            found, removed = await compute_card_innovations(session, dry_run=dry_run)
            result.innovations_found = found
            result.innovations_removed = removed
        except Exception as e:
            msg = f"Error computing card innovations: {e}"
            logger.error(msg, exc_info=True)
            result.errors.append(msg)

        if not dry_run:
            await session.commit()

    logger.info(
        "JP intelligence complete: archetypes=%d/%d, innovations=%d/%d, errors=%d",
        result.new_archetypes_found,
        result.new_archetypes_removed,
        result.innovations_found,
        result.innovations_removed,
        len(result.errors),
    )
    return result
