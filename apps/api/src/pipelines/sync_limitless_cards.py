"""Pipeline for syncing Limitless EN card IDs to the Card table."""

import logging
from dataclasses import dataclass, field

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import (
    LimitlessClient,
    LimitlessENCard,
    LimitlessError,
    map_set_code,
)
from src.db.database import async_session_factory
from src.models.card import Card
from src.routers.meta import _generate_card_id_variants

logger = logging.getLogger(__name__)


@dataclass
class SyncLimitlessCardsResult:
    """Result of a Limitless card sync operation."""

    sets_processed: int = 0
    cards_found: int = 0
    cards_mapped: int = 0
    cards_unmatched: int = 0
    errors: list[str] = field(default_factory=list)
    unmatched_by_set: dict[str, list[str]] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _build_tcgdex_candidates(card: LimitlessENCard) -> list[str]:
    """Build candidate TCGdex IDs for a Limitless EN card.

    Maps the Limitless set code to TCGdex set ID, then generates
    padded/unpadded variants of the full card ID.
    """
    tcgdex_set = map_set_code(card.set_code)
    base_id = f"{tcgdex_set}-{card.card_number}"
    return _generate_card_id_variants(base_id)


async def _sync_set(
    session: AsyncSession,
    client: LimitlessClient,
    set_code: str,
) -> tuple[int, int, int, list[str]]:
    """Sync Limitless IDs for a single EN set.

    Returns:
        Tuple of (cards_found, cards_mapped, cards_unmatched,
        unmatched_ids).
    """
    cards = await client.fetch_en_set_cards(set_code)
    if not cards:
        return 0, 0, 0, []

    mapped = 0
    unmatched = 0
    unmatched_ids: list[str] = []

    for card in cards:
        limitless_id = card.limitless_id
        candidates = _build_tcgdex_candidates(card)

        if not candidates:
            unmatched += 1
            unmatched_ids.append(limitless_id)
            continue

        # Find matching Card record
        result = await session.execute(select(Card.id).where(Card.id.in_(candidates)))
        row = result.first()

        if row:
            await session.execute(
                update(Card).where(Card.id == row[0]).values(limitless_id=limitless_id)
            )
            mapped += 1
        else:
            unmatched += 1
            unmatched_ids.append(limitless_id)
            logger.debug(
                "No TCGdex match for %s (tried %s)",
                limitless_id,
                candidates[:3],
            )

    await session.flush()
    return len(cards), mapped, unmatched, unmatched_ids


async def sync_limitless_cards(
    dry_run: bool = False,
    sets: list[str] | None = None,
) -> SyncLimitlessCardsResult:
    """Sync Limitless EN card IDs to the Card table.

    For each EN card on Limitless, constructs the Limitless-format ID
    (e.g., "OBF-125") and maps it to the corresponding TCGdex Card
    record via variant matching. Sets card.limitless_id on match.

    Args:
        dry_run: If True, don't commit changes.
        sets: Optional list of set codes to sync. If None, syncs all.
    """
    result = SyncLimitlessCardsResult()

    async with LimitlessClient() as client:
        try:
            if sets:
                set_codes = [s.upper() for s in sets]
            else:
                set_codes = await client.fetch_en_sets()

            logger.info(
                "Syncing Limitless card IDs for %d sets (dry_run=%s)",
                len(set_codes),
                dry_run,
            )
        except LimitlessError as e:
            result.errors.append(f"Failed to fetch EN sets: {e}")
            return result

        async with async_session_factory() as session:
            for set_code in set_codes:
                try:
                    found, mapped, unmatched, unmatched_ids = await _sync_set(
                        session, client, set_code
                    )
                    result.sets_processed += 1
                    result.cards_found += found
                    result.cards_mapped += mapped
                    result.cards_unmatched += unmatched
                    if unmatched_ids:
                        result.unmatched_by_set[set_code] = unmatched_ids

                    logger.info(
                        "Set %s: found=%d, mapped=%d, unmatched=%d",
                        set_code,
                        found,
                        mapped,
                        unmatched,
                    )
                except LimitlessError as e:
                    msg = f"Error syncing set {set_code}: {e}"
                    logger.warning(msg)
                    result.errors.append(msg)

            if dry_run:
                await session.rollback()
                logger.info("Dry run — rolled back all changes")
            else:
                await session.commit()
                logger.info(
                    "Committed: %d cards mapped across %d sets",
                    result.cards_mapped,
                    result.sets_processed,
                )

    return result
