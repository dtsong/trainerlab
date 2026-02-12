"""JP card adoption rate sync pipeline.

Fetches card adoption rate data from Pokecabook and syncs to database.
"""

from __future__ import annotations

import hashlib
import inspect
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.pokecabook import PokecabookClient, PokecabookError
from src.db.database import async_session_factory
from src.models.card import Card
from src.models.card_id_mapping import CardIdMapping
from src.models.jp_card_adoption_rate import JPCardAdoptionRate
from src.models.set import Set
from src.services.pipeline_resilience import retry_commit, with_timeout

FETCH_TIMEOUT = 30  # seconds for external HTTP call

logger = logging.getLogger(__name__)


async def _maybe_await(value: Any) -> Any:
    """Await value only when it is awaitable."""
    if inspect.isawaitable(value):
        return await value
    return value


@dataclass
class SyncAdoptionRatesResult:
    """Result of adoption rate sync pipeline."""

    rates_fetched: int = 0
    rates_created: int = 0
    rates_updated: int = 0
    rates_skipped: int = 0
    rates_backfilled: int = 0
    mapping_resolved: int = 0
    mapping_unresolved: int = 0
    mapping_coverage: float = 0.0
    mapped_by_method: dict[str, int] = field(default_factory=dict)
    unmapped_by_source: dict[str, int] = field(default_factory=dict)
    unmapped_by_set: dict[str, int] = field(default_factory=dict)
    unmapped_card_samples: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


@dataclass
class CardResolution:
    """Resolved card identity for adoption records."""

    card_id: str
    method: str
    set_id: str | None = None


def _normalize_card_name(name: str | None) -> str:
    """Normalize card names for fuzzy matching across sources."""
    if not name:
        return ""
    normalized = name.casefold()
    normalized = normalized.replace("’", "'")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


async def _resolve_card_for_adoption_entry(
    session: AsyncSession,
    card_name_jp: str | None,
    card_name_en: str | None,
    cache: dict[tuple[str, str], CardResolution | None],
) -> CardResolution:
    """Resolve adoption entry to canonical card ID using fallback chain."""

    def _cache_key(source: str, value: str | None) -> tuple[str, str] | None:
        normalized = _normalize_card_name(value)
        if not normalized:
            return None
        return (source, normalized)

    en_key = _cache_key("en", card_name_en)
    if en_key:
        cached = cache.get(en_key)
        if cached is not None:
            return cached

        query = (
            select(Card.id, Card.set_id)
            .join(Set, Card.set_id == Set.id, isouter=True)
            .where(func.lower(Card.name) == en_key[1])
            .order_by(Set.release_date.desc().nullslast(), Card.id.asc())
            .limit(1)
        )
        row = (await session.execute(query)).first()
        if row:
            resolved = CardResolution(
                card_id=row.id, method="card_name_en", set_id=row.set_id
            )
            cache[en_key] = resolved
            return resolved

    jp_key = _cache_key("jp", card_name_jp)
    if jp_key:
        cached = cache.get(jp_key)
        if cached is not None:
            return cached

        query = (
            select(Card.id, Card.set_id)
            .join(Set, Card.set_id == Set.id, isouter=True)
            .where(func.lower(Card.japanese_name) == jp_key[1])
            .order_by(Set.release_date_jp.desc().nullslast(), Card.id.asc())
            .limit(1)
        )
        row = (await session.execute(query)).first()
        if row:
            resolved = CardResolution(
                card_id=row.id, method="card_name_jp", set_id=row.set_id
            )
            cache[jp_key] = resolved
            return resolved

    if en_key:
        mapping_query = (
            select(CardIdMapping.en_card_id, CardIdMapping.en_set_id)
            .where(
                CardIdMapping.card_name_en.isnot(None),
                func.lower(CardIdMapping.card_name_en) == en_key[1],
            )
            .order_by(CardIdMapping.confidence.desc(), CardIdMapping.updated_at.desc())
            .limit(1)
        )
        mapping_row = (await session.execute(mapping_query)).first()
        if mapping_row and mapping_row.en_card_id:
            resolved = CardResolution(
                card_id=mapping_row.en_card_id,
                method="mapping_name_en",
                set_id=mapping_row.en_set_id,
            )
            cache[en_key] = resolved
            return resolved

    fallback_name = card_name_jp or card_name_en or "unknown"
    return CardResolution(
        card_id=_generate_card_id(fallback_name),
        method="generated_hash",
        set_id=None,
    )


async def backfill_adoption_card_ids(
    session: AsyncSession,
    lookback_days: int = 90,
) -> int:
    """Backfill unresolved adoption rows after new mappings arrive."""
    cutoff = date.today() - timedelta(days=lookback_days)
    unresolved_query = select(JPCardAdoptionRate).where(
        JPCardAdoptionRate.period_end >= cutoff,
        or_(
            JPCardAdoptionRate.card_id.like("jp-%"),
            JPCardAdoptionRate.card_id.like("unmapped-%"),
        ),
    )
    unresolved_result = await session.execute(unresolved_query)
    try:
        scalars_result = await _maybe_await(unresolved_result.scalars())
        unresolved_rows = await _maybe_await(scalars_result.all())
    except Exception:
        logger.warning("Could not read unresolved adoption rows for backfill")
        return 0

    cache: dict[tuple[str, str], CardResolution | None] = {}
    updated = 0
    for row in unresolved_rows:
        resolved = await _resolve_card_for_adoption_entry(
            session,
            row.card_name_jp,
            row.card_name_en,
            cache,
        )
        if resolved.method == "generated_hash":
            continue
        if row.card_id != resolved.card_id:
            row.card_id = resolved.card_id
            updated += 1

    return updated


async def sync_adoption_rates(
    dry_run: bool = False,
) -> SyncAdoptionRatesResult:
    """Sync card adoption rates from Pokecabook.

    Fetches current adoption rate data and stores in the database,
    tracking historical rates over time.

    Args:
        dry_run: If True, fetch data but don't persist.

    Returns:
        SyncAdoptionRatesResult with statistics.
    """
    result = SyncAdoptionRatesResult()

    logger.info("Starting adoption rate sync: dry_run=%s", dry_run)

    try:
        async with PokecabookClient() as pokecabook:
            adoption_data = await with_timeout(
                pokecabook.fetch_adoption_rates(),
                FETCH_TIMEOUT,
                pipeline="sync-jp-adoption-rates",
                step="fetch-adoption-rates",
            )

            result.rates_fetched = len(adoption_data.entries)
            logger.info("Fetched %d adoption rate entries", len(adoption_data.entries))

            if dry_run:
                logger.info(
                    "DRY RUN: Would sync %d adoption rate entries",
                    len(adoption_data.entries),
                )
                return result

            async with async_session_factory() as session:
                today = date.today()
                period_start = today - timedelta(days=7)
                period_end = today
                resolution_cache: dict[tuple[str, str], CardResolution | None] = {}

                for entry in adoption_data.entries:
                    try:
                        if not entry.card_name_jp or entry.inclusion_rate <= 0:
                            result.rates_skipped += 1
                            continue

                        resolution = await _resolve_card_for_adoption_entry(
                            session,
                            entry.card_name_jp,
                            entry.card_name_en,
                            resolution_cache,
                        )
                        card_id = resolution.card_id

                        result.mapped_by_method[resolution.method] = (
                            result.mapped_by_method.get(resolution.method, 0) + 1
                        )
                        if resolution.method == "generated_hash":
                            result.mapping_unresolved += 1
                            source_key = adoption_data.source_url or "unknown"
                            result.unmapped_by_source[source_key] = (
                                result.unmapped_by_source.get(source_key, 0) + 1
                            )
                            set_key = resolution.set_id or "unknown"
                            result.unmapped_by_set[set_key] = (
                                result.unmapped_by_set.get(set_key, 0) + 1
                            )

                            sample_name = (
                                entry.card_name_jp or entry.card_name_en or card_id
                            )
                            if (
                                sample_name
                                and sample_name not in result.unmapped_card_samples
                                and len(result.unmapped_card_samples) < 25
                            ):
                                result.unmapped_card_samples.append(sample_name)
                        else:
                            result.mapping_resolved += 1

                        existing_query = select(JPCardAdoptionRate).where(
                            JPCardAdoptionRate.card_id == card_id,
                            JPCardAdoptionRate.period_start == period_start,
                            JPCardAdoptionRate.period_end == period_end,
                        )
                        existing_result = await session.execute(existing_query)
                        existing = existing_result.scalar_one_or_none()

                        if existing:
                            existing.inclusion_rate = entry.inclusion_rate
                            existing.avg_copies = entry.avg_copies
                            existing.archetype_context = entry.archetype
                            existing.source_url = adoption_data.source_url
                            existing.raw_data = {
                                "mapping_method": resolution.method,
                                "mapped_set_id": resolution.set_id,
                            }
                            result.rates_updated += 1
                        else:
                            new_rate = JPCardAdoptionRate(
                                id=uuid4(),
                                card_id=card_id,
                                card_name_jp=entry.card_name_jp,
                                card_name_en=entry.card_name_en,
                                inclusion_rate=entry.inclusion_rate,
                                avg_copies=entry.avg_copies,
                                archetype_context=entry.archetype,
                                period_start=period_start,
                                period_end=period_end,
                                source="pokecabook",
                                source_url=adoption_data.source_url,
                                raw_data={
                                    "mapping_method": resolution.method,
                                    "mapped_set_id": resolution.set_id,
                                },
                            )
                            session.add(new_rate)
                            result.rates_created += 1

                    except SQLAlchemyError as e:
                        error_msg = f"Error saving rate for {entry.card_name_jp}: {e}"
                        logger.warning(error_msg)
                        result.errors.append(error_msg)

                try:
                    result.rates_backfilled = await backfill_adoption_card_ids(session)
                except Exception:
                    logger.warning(
                        "Adoption backfill failed (non-fatal)", exc_info=True
                    )
                    result.rates_backfilled = 0

                total_considered = result.mapping_resolved + result.mapping_unresolved
                if total_considered > 0:
                    result.mapping_coverage = result.mapping_resolved / total_considered

                await retry_commit(session, context="sync-adoption-rates")

    except PokecabookError as e:
        error_msg = f"Error fetching adoption rates: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)
    except Exception as e:
        error_msg = f"Pipeline error: {e}"
        logger.error(error_msg, exc_info=True)
        result.errors.append(error_msg)

    logger.info(
        "Adoption sync complete: fetched=%d created=%d updated=%d "
        "backfilled=%d coverage=%.2f unresolved=%d errors=%d",
        result.rates_fetched,
        result.rates_created,
        result.rates_updated,
        result.rates_backfilled,
        result.mapping_coverage,
        result.mapping_unresolved,
        len(result.errors),
    )

    return result


def _generate_card_id(card_name_jp: str) -> str:
    """Generate a stable card ID from Japanese card name.

    Uses a hash-based approach since we don't have set/number info
    from adoption rate data.
    """
    name_hash = hashlib.sha256(card_name_jp.encode()).hexdigest()[:8]
    return f"jp-{name_hash}"
