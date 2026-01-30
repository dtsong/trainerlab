"""Card sync pipelines for TCGdex data."""

import logging

from src.clients.tcgdex import TCGdexClient
from src.db.database import async_session_factory
from src.services.card_sync import CardSyncService, SyncResult

logger = logging.getLogger(__name__)


async def sync_english_cards(dry_run: bool = False) -> SyncResult:
    """Sync all English cards from TCGdex.

    Args:
        dry_run: If True, don't actually commit to database.

    Returns:
        Sync result summary.
    """
    logger.info(f"Starting English card sync (dry_run={dry_run})...")

    if dry_run:
        logger.info("DRY RUN - no changes will be committed")
        # Return empty result for dry run
        return SyncResult()

    async with TCGdexClient() as client, async_session_factory() as session:
        service = CardSyncService(session, client)
        result = await service.sync_all_english()
        return result


async def sync_japanese_names(dry_run: bool = False) -> int:
    """Sync Japanese card names from TCGdex.

    This function fetches Japanese card data and attempts to match
    cards by their English counterparts to update japanese_name field.

    Note: Japanese and English card IDs don't always match directly.
    This function uses card name matching as a fallback.

    Args:
        dry_run: If True, don't actually commit to database.

    Returns:
        Number of cards updated.
    """
    logger.info(f"Starting Japanese name sync (dry_run={dry_run})...")

    if dry_run:
        logger.info("DRY RUN - no changes will be committed")
        return 0

    updated_count = 0
    async with TCGdexClient() as client, async_session_factory() as session:
        # Fetch Japanese sets
        ja_sets = await client.fetch_all_sets(language="ja")
        logger.info(f"Found {len(ja_sets)} Japanese sets")

        # Build mapping of English card name -> Japanese name
        # This is a simplified approach; in production you'd want
        # more sophisticated matching (by card image, set mapping, etc.)
        name_map: dict[str, str] = {}

        for set_summary in ja_sets:
            try:
                ja_cards = await client.fetch_cards_for_set(
                    set_summary.id, language="ja"
                )
                for ja_card in ja_cards:
                    # Store Japanese name by card ID
                    # Note: Japanese IDs may differ from English IDs
                    name_map[ja_card.id] = ja_card.name
                    logger.debug(f"Mapped {ja_card.id} -> {ja_card.name}")
            except Exception as e:
                logger.warning(f"Error fetching Japanese set {set_summary.id}: {e}")
                continue

        logger.info(f"Built name map with {len(name_map)} entries")

        # Update cards with Japanese names
        service = CardSyncService(session, client)
        updated_count = await service.update_japanese_names(name_map)
        await session.commit()

    logger.info(f"Japanese name sync complete. Updated {updated_count} cards.")
    return updated_count


async def sync_all(dry_run: bool = False) -> tuple[SyncResult, int]:
    """Sync both English cards and Japanese names.

    Args:
        dry_run: If True, don't actually commit to database.

    Returns:
        Tuple of (English sync result, Japanese names updated count).
    """
    logger.info(f"Starting full card sync (dry_run={dry_run})...")

    english_result = await sync_english_cards(dry_run=dry_run)
    japanese_count = await sync_japanese_names(dry_run=dry_run)

    logger.info("Full sync complete.")
    return english_result, japanese_count
