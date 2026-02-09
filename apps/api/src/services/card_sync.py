"""Card sync service for TCGdex data."""

import logging
from dataclasses import dataclass, field

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.tcgdex import TCGdexCard, TCGdexClient, TCGdexError, TCGdexSet
from src.models.card import Card
from src.models.set import Set

logger = logging.getLogger(__name__)

# TCGdex JP set ID -> Limitless-normalized set ID
TCGDEX_JP_TO_LIMITLESS_SET: dict[str, str] = {
    "SV9": "sv09",
    "SV8a": "sv08.5",
    "SV8": "sv08",
    "SV7a": "sv7",
    "SV7": "sv7",
    "SV6a": "sv6pt5",
    "SV6": "sv6",
    "SV5a": "sv5",
    "SV5K": "sv5",
    "SV5M": "sv5",
    "SV4a": "sv4",
    "SV4K": "sv4",
    "SV4M": "sv4",
    "SV3a": "sv3",
    "SV3": "sv3",
    "SV2a": "sv2",
    "SV2D": "sv2",
    "SV2P": "sv2",
    "SV1a": "sv1",
    "SV1S": "sv1",
    "SV1V": "sv1",
    "SVME1": "me01",
    "SVME2": "me02",
    "SVMEE": "mee",
}

# JP sets to sync (modern SV-era sets appearing in current JP decklists)
JP_SETS_TO_SYNC: list[str] = [
    "SV9",
    "SV8a",
    "SV8",
    "SV7a",
    "SV7",
    "SV6a",
    "SV6",
    "SV5a",
    "SV5K",
    "SV5M",
    "SV4a",
    "SV4K",
    "SV4M",
    "SV3a",
    "SV3",
    "SV2a",
    "SV2D",
    "SV2P",
    "SV1a",
    "SV1S",
    "SV1V",
    "SVME1",
    "SVME2",
    "SVMEE",
]


def normalize_jp_card_id(tcgdex_id: str, tcgdex_set_id: str) -> str | None:
    """Convert TCGdex JP card ID to Limitless-normalized format.

    Examples:
        SV9-097 -> sv09-97
        SV6a-042 -> sv6pt5-42

    Args:
        tcgdex_id: TCGdex card ID (e.g., "SV9-097").
        tcgdex_set_id: TCGdex set ID (e.g., "SV9").

    Returns:
        Limitless-normalized card ID, or None if set is unknown.
    """
    limitless_set = TCGDEX_JP_TO_LIMITLESS_SET.get(tcgdex_set_id)
    if not limitless_set:
        return None
    local_id = tcgdex_id.split("-", 1)[-1]
    try:
        card_number = str(int(local_id))
    except ValueError:
        # Non-numeric local ID (e.g., promo suffixes)
        card_number = local_id.lstrip("0") or "0"
    return f"{limitless_set}-{card_number}"


def tcgdex_set_to_db_set(tcgdex_set: TCGdexSet) -> Set:
    """Convert TCGdex set to database set model.

    Args:
        tcgdex_set: TCGdex set data.

    Returns:
        Database Set model.
    """
    legalities = None
    if tcgdex_set.legal_standard is not None or tcgdex_set.legal_expanded is not None:
        legalities = {}
        if tcgdex_set.legal_standard is not None:
            legalities["standard"] = tcgdex_set.legal_standard
        if tcgdex_set.legal_expanded is not None:
            legalities["expanded"] = tcgdex_set.legal_expanded

    return Set(
        id=tcgdex_set.id,
        name=tcgdex_set.name,
        series=tcgdex_set.series_name,
        release_date=tcgdex_set.release_date,
        card_count=tcgdex_set.card_count_official,
        logo_url=tcgdex_set.logo,
        symbol_url=tcgdex_set.symbol,
        legalities=legalities,
    )


def tcgdex_card_to_db_card(tcgdex_card: TCGdexCard) -> Card:
    """Convert TCGdex card to database card model.

    Args:
        tcgdex_card: TCGdex card data.

    Returns:
        Database Card model.
    """
    legalities = None
    if tcgdex_card.legal_standard is not None or tcgdex_card.legal_expanded is not None:
        legalities = {}
        if tcgdex_card.legal_standard is not None:
            legalities["standard"] = tcgdex_card.legal_standard
        if tcgdex_card.legal_expanded is not None:
            legalities["expanded"] = tcgdex_card.legal_expanded

    return Card(
        id=tcgdex_card.id,
        local_id=tcgdex_card.local_id,
        name=tcgdex_card.name,
        supertype=tcgdex_card.supertype,
        subtypes=tcgdex_card.subtypes,
        types=tcgdex_card.types,
        hp=tcgdex_card.hp,
        stage=tcgdex_card.stage,
        evolves_from=tcgdex_card.evolves_from,
        evolves_to=tcgdex_card.evolves_to,
        attacks=tcgdex_card.attacks,
        abilities=tcgdex_card.abilities,
        weaknesses=tcgdex_card.weaknesses,
        resistances=tcgdex_card.resistances,
        retreat_cost=tcgdex_card.retreat_cost,
        rules=tcgdex_card.rules,
        set_id=tcgdex_card.set_id,
        rarity=tcgdex_card.rarity,
        number=tcgdex_card.number,
        image_small=tcgdex_card.image_small,
        image_large=tcgdex_card.image_large,
        regulation_mark=tcgdex_card.regulation_mark,
        legalities=legalities,
    )


@dataclass
class SyncResult:
    """Result of a sync operation."""

    sets_processed: int = 0
    sets_inserted: int = 0
    sets_updated: int = 0
    cards_processed: int = 0
    cards_inserted: int = 0
    cards_updated: int = 0
    errors: list[str] = field(default_factory=list)


class CardSyncService:
    """Service for syncing card data from TCGdex to database."""

    def __init__(self, session: AsyncSession, client: TCGdexClient):
        """Initialize card sync service.

        Args:
            session: Database session.
            client: TCGdex API client.
        """
        self._session = session
        self._client = client
        self.result = SyncResult()

    async def upsert_set(self, db_set: Set) -> None:
        """Insert or update a set.

        Args:
            db_set: Set to upsert.
        """
        existing = await self._session.get(Set, db_set.id)
        if existing is None:
            self._session.add(db_set)
            self.result.sets_inserted += 1
        else:
            # Update existing set fields
            existing.name = db_set.name
            existing.series = db_set.series
            existing.release_date = db_set.release_date
            existing.release_date_jp = db_set.release_date_jp
            existing.card_count = db_set.card_count
            existing.logo_url = db_set.logo_url
            existing.symbol_url = db_set.symbol_url
            existing.legalities = db_set.legalities
            self.result.sets_updated += 1

    async def upsert_cards(self, cards: list[Card], batch_size: int = 100) -> None:
        """Insert or update cards in batches.

        Args:
            cards: Cards to upsert.
            batch_size: Number of cards per batch.
        """
        for i in range(0, len(cards), batch_size):
            batch = cards[i : i + batch_size]
            for card in batch:
                await self._session.merge(card)
                self.result.cards_processed += 1
            await self._session.flush()

    async def sync_set(self, set_id: str, language: str = "en") -> None:
        """Sync a single set and its cards from TCGdex.

        Args:
            set_id: Set ID to sync.
            language: Language code.
        """
        logger.info(f"Syncing set {set_id} ({language})...")

        try:
            # Fetch set details
            tcgdex_set = await self._client.fetch_set(set_id, language)
            db_set = tcgdex_set_to_db_set(tcgdex_set)
            await self.upsert_set(db_set)
            self.result.sets_processed += 1

            # Fetch and sync all cards for the set
            tcgdex_cards = await self._client.fetch_cards_for_set(set_id, language)
            db_cards = [tcgdex_card_to_db_card(c) for c in tcgdex_cards]
            await self.upsert_cards(db_cards)

            logger.info(
                f"Set {set_id}: {len(db_cards)} cards synced "
                f"(inserted: {self.result.cards_inserted}, "
                f"updated: {self.result.cards_updated})"
            )
        except (TCGdexError, httpx.RequestError, httpx.HTTPStatusError) as e:
            error_msg = f"Error syncing set {set_id}: {e}"
            logger.error(error_msg)
            self.result.errors.append(error_msg)

    async def sync_all_english(self) -> SyncResult:
        """Sync all English sets and cards.

        Returns:
            Sync result summary.
        """
        logger.info("Starting English card sync...")

        # Fetch all set summaries
        set_summaries = await self._client.fetch_all_sets(language="en")
        logger.info(f"Found {len(set_summaries)} English sets")

        # Sync each set
        for i, summary in enumerate(set_summaries, 1):
            logger.info(f"Processing set {i}/{len(set_summaries)}: {summary.name}")
            await self.sync_set(summary.id, language="en")
            await self._session.commit()

        logger.info(
            f"English sync complete. "
            f"Sets: {self.result.sets_processed} processed, "
            f"{self.result.sets_inserted} inserted, "
            f"{self.result.sets_updated} updated. "
            f"Cards: {self.result.cards_processed} processed. "
            f"Errors: {len(self.result.errors)}"
        )
        return self.result

    async def sync_jp_set(self, tcgdex_set_id: str) -> None:
        """Sync a single JP set from TCGdex.

        Fetches JP cards, normalizes IDs to Limitless format, and
        inserts new cards or backfills japanese_name on existing ones.

        Args:
            tcgdex_set_id: TCGdex JP set ID (e.g., "SV9").
        """
        limitless_set_id = TCGDEX_JP_TO_LIMITLESS_SET.get(tcgdex_set_id)
        if not limitless_set_id:
            error = f"Unknown JP set: {tcgdex_set_id}"
            logger.warning(error)
            self.result.errors.append(error)
            return

        logger.info(
            "Syncing JP set %s -> %s...",
            tcgdex_set_id,
            limitless_set_id,
        )

        try:
            tcgdex_set = await self._client.fetch_set(tcgdex_set_id, language="ja")

            # Upsert the set using Limitless-normalized ID
            db_set = Set(
                id=limitless_set_id,
                name=tcgdex_set.name,
                series=tcgdex_set.series_name,
                release_date=tcgdex_set.release_date,
                card_count=tcgdex_set.card_count_official,
                logo_url=tcgdex_set.logo,
                symbol_url=tcgdex_set.symbol,
            )
            await self.upsert_set(db_set)
            self.result.sets_processed += 1

            # Fetch all cards for this set
            tcgdex_cards = await self._client.fetch_cards_for_set(
                tcgdex_set_id, language="ja"
            )

            for tc in tcgdex_cards:
                norm_id = normalize_jp_card_id(tc.id, tcgdex_set_id)
                if not norm_id:
                    continue

                existing = await self._session.get(Card, norm_id)
                if existing:
                    # Only backfill japanese_name if missing
                    if not existing.japanese_name:
                        existing.japanese_name = tc.name
                    self.result.cards_updated += 1
                else:
                    # Insert new JP-only card
                    db_card = Card(
                        id=norm_id,
                        local_id=tc.local_id,
                        name=tc.name,
                        japanese_name=tc.name,
                        supertype=tc.supertype,
                        subtypes=tc.subtypes,
                        types=tc.types,
                        hp=tc.hp,
                        stage=tc.stage,
                        evolves_from=tc.evolves_from,
                        evolves_to=tc.evolves_to,
                        attacks=tc.attacks,
                        abilities=tc.abilities,
                        weaknesses=tc.weaknesses,
                        resistances=tc.resistances,
                        retreat_cost=tc.retreat_cost,
                        rules=tc.rules,
                        set_id=limitless_set_id,
                        rarity=tc.rarity,
                        number=tc.number,
                        image_small=tc.image_small,
                        image_large=tc.image_large,
                        regulation_mark=tc.regulation_mark,
                    )
                    self._session.add(db_card)
                    self.result.cards_inserted += 1

                self.result.cards_processed += 1

            await self._session.flush()

            logger.info(
                "JP set %s: %d cards synced (inserted: %d, updated: %d)",
                tcgdex_set_id,
                len(tcgdex_cards),
                self.result.cards_inserted,
                self.result.cards_updated,
            )
        except (
            TCGdexError,
            httpx.RequestError,
            httpx.HTTPStatusError,
        ) as e:
            error_msg = f"Error syncing JP set {tcgdex_set_id}: {e}"
            logger.error(error_msg)
            self.result.errors.append(error_msg)

    async def sync_all_japanese(self) -> SyncResult:
        """Sync all JP sets and cards from TCGdex.

        Returns:
            Sync result summary.
        """
        logger.info("Starting Japanese card sync...")

        for i, tcgdex_set_id in enumerate(JP_SETS_TO_SYNC, 1):
            logger.info(
                "Processing JP set %d/%d: %s",
                i,
                len(JP_SETS_TO_SYNC),
                tcgdex_set_id,
            )
            await self.sync_jp_set(tcgdex_set_id)
            await self._session.commit()

        logger.info(
            "Japanese sync complete. "
            "Sets: %d processed, %d inserted, %d updated. "
            "Cards: %d processed, %d inserted, %d updated. "
            "Errors: %d",
            self.result.sets_processed,
            self.result.sets_inserted,
            self.result.sets_updated,
            self.result.cards_processed,
            self.result.cards_inserted,
            self.result.cards_updated,
            len(self.result.errors),
        )
        return self.result

    async def update_japanese_names(
        self, name_map: dict[str, str], batch_size: int = 100
    ) -> int:
        """Update Japanese names for cards.

        Args:
            name_map: Mapping of card ID to Japanese name.
            batch_size: Number of cards per batch.

        Returns:
            Number of cards updated.
        """
        updated = 0
        card_ids = list(name_map.keys())

        for i in range(0, len(card_ids), batch_size):
            batch_ids = card_ids[i : i + batch_size]
            for card_id in batch_ids:
                card = await self._session.get(Card, card_id)
                if card:
                    card.japanese_name = name_map[card_id]
                    updated += 1
            await self._session.flush()

        logger.info(f"Updated Japanese names for {updated} cards")
        return updated
