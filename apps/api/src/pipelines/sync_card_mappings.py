"""Pipeline for syncing JP-to-EN card ID mappings from Limitless."""

import logging
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import LimitlessClient, LimitlessError
from src.db.database import async_session_factory
from src.models import CardIdMapping
from src.pipelines.sync_jp_adoption_rates import backfill_adoption_card_ids

logger = logging.getLogger(__name__)


@dataclass
class SyncMappingsResult:
    """Result of a card mapping sync operation."""

    sets_processed: int = 0
    mappings_found: int = 0
    mappings_inserted: int = 0
    mappings_updated: int = 0
    adoption_rows_backfilled: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def sync_card_mappings_for_set(
    session: AsyncSession,
    client: LimitlessClient,
    jp_set_id: str,
) -> tuple[int, int]:
    """Sync card mappings for a single JP set.

    Args:
        session: Database session.
        client: Limitless HTTP client.
        jp_set_id: Japanese set code to sync.

    Returns:
        Tuple of (inserted_count, updated_count).
    """
    equivalents = await client.fetch_card_equivalents(jp_set_id)

    if not equivalents:
        logger.info("No equivalents found for JP set %s", jp_set_id)
        return 0, 0

    existing_query = select(CardIdMapping.jp_card_id).where(
        CardIdMapping.jp_set_id == jp_set_id
    )
    existing_result = await session.execute(existing_query)
    existing_ids = {row[0] for row in existing_result}

    inserted = 0
    updated = 0

    for equiv in equivalents:
        is_update = equiv.jp_card_id in existing_ids

        stmt = pg_insert(CardIdMapping).values(
            id=uuid4(),
            jp_card_id=equiv.jp_card_id,
            en_card_id=equiv.en_card_id,
            card_name_en=equiv.card_name_en,
            jp_set_id=equiv.jp_set_id,
            en_set_id=equiv.en_set_id,
            confidence=1.0,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["jp_card_id"],
            set_={
                "en_card_id": stmt.excluded.en_card_id,
                "card_name_en": stmt.excluded.card_name_en,
                "en_set_id": stmt.excluded.en_set_id,
            },
        )

        await session.execute(stmt)

        if is_update:
            updated += 1
        else:
            inserted += 1

    await session.commit()
    logger.info(
        "Synced JP set %s: %d inserted, %d updated",
        jp_set_id,
        inserted,
        updated,
    )

    return inserted, updated


async def sync_all_card_mappings(
    jp_sets: list[str] | None = None,
    dry_run: bool = False,
) -> SyncMappingsResult:
    """Sync card mappings for all JP sets.

    Args:
        jp_sets: Optional list of specific JP set codes to sync.
                 If None, fetches all available JP sets from Limitless.
        dry_run: If True, don't commit changes to database.

    Returns:
        SyncMappingsResult with statistics.
    """
    result = SyncMappingsResult()

    logger.info("Starting card mapping sync (dry_run=%s)", dry_run)

    if dry_run:
        logger.info("DRY RUN - no changes will be committed")
        return result

    async with LimitlessClient() as client:
        if jp_sets is None:
            try:
                jp_sets = await client.fetch_jp_sets()
            except LimitlessError as e:
                error_msg = f"Error fetching JP set list: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result

        async with async_session_factory() as session:
            for jp_set_id in jp_sets:
                try:
                    inserted, updated = await sync_card_mappings_for_set(
                        session, client, jp_set_id
                    )
                    result.sets_processed += 1
                    result.mappings_inserted += inserted
                    result.mappings_updated += updated
                    result.mappings_found += inserted + updated

                except LimitlessError as e:
                    error_msg = f"Error syncing JP set {jp_set_id}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    continue

            try:
                result.adoption_rows_backfilled = await backfill_adoption_card_ids(
                    session
                )
                if result.adoption_rows_backfilled > 0:
                    await session.commit()
            except Exception as e:  # pragma: no cover - defensive logging path
                logger.warning(
                    "Error backfilling adoption mappings (non-fatal): %s",
                    e,
                )

    logger.info(
        "Card mapping sync complete: sets=%d, found=%d, inserted=%d, "
        "updated=%d, adoption_backfilled=%d",
        result.sets_processed,
        result.mappings_found,
        result.mappings_inserted,
        result.mappings_updated,
        result.adoption_rows_backfilled,
    )
    if result.errors:
        logger.info("Errors: %d", len(result.errors))

    return result


async def sync_recent_jp_sets(
    lookback_sets: int = 5,
    dry_run: bool = False,
) -> SyncMappingsResult:
    """Sync card mappings for recent JP sets only.

    Useful for incremental updates when new sets are released.

    Args:
        lookback_sets: Number of most recent JP sets to sync.
        dry_run: If True, don't commit changes.

    Returns:
        SyncMappingsResult with statistics.
    """
    logger.info("Syncing recent %d JP sets", lookback_sets)

    async with LimitlessClient() as client:
        try:
            all_sets = await client.fetch_jp_sets()
        except LimitlessError as e:
            result = SyncMappingsResult()
            result.errors.append(f"Error fetching JP set list: {e}")
            return result

    recent_sets = all_sets[:lookback_sets]
    logger.info("Recent JP sets to sync: %s", recent_sets)

    return await sync_all_card_mappings(jp_sets=recent_sets, dry_run=dry_run)


async def get_jp_to_en_mapping(session: AsyncSession) -> dict[str, str]:
    """Load the JP-to-EN card ID mapping from database.

    Args:
        session: Database session.

    Returns:
        Dict mapping JP card IDs to EN card IDs.
    """
    query = select(CardIdMapping.jp_card_id, CardIdMapping.en_card_id)
    result = await session.execute(query)

    mapping = {row.jp_card_id: row.en_card_id for row in result}
    logger.debug("Loaded %d JP-to-EN card mappings", len(mapping))

    return mapping


async def get_en_to_jp_mapping(session: AsyncSession) -> dict[str, list[str]]:
    """Load the EN-to-JP card ID mapping from database.

    An EN card can have multiple JP equivalents (different sets/printings).

    Args:
        session: Database session.

    Returns:
        Dict mapping EN card IDs to lists of JP card IDs.
    """
    query = select(CardIdMapping.en_card_id, CardIdMapping.jp_card_id)
    result = await session.execute(query)

    mapping: dict[str, list[str]] = {}
    for row in result:
        if row.en_card_id not in mapping:
            mapping[row.en_card_id] = []
        mapping[row.en_card_id].append(row.jp_card_id)

    logger.debug("Loaded %d EN-to-JP card mappings", len(mapping))

    return mapping
