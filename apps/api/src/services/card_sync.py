"""Card sync service for TCGdex data."""

import logging
from dataclasses import dataclass, field

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.tcgdex import TCGdexCard, TCGdexClient, TCGdexError, TCGdexSet
from src.models.card import Card
from src.models.set import Set

logger = logging.getLogger(__name__)


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
