"""Tests for card sync service."""

from datetime import date
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.tcgdex import TCGdexCard, TCGdexSet, TCGdexSetSummary
from src.models.card import Card
from src.models.set import Set
from src.services.card_sync import (
    CardSyncService,
    SyncResult,
    tcgdex_card_to_db_card,
    tcgdex_set_to_db_set,
)


class TestTcgdexToDbMapping:
    """Tests for TCGdex to database mapping functions."""

    def test_tcgdex_set_to_db_set(self):
        """Test converting TCGdex set to database set."""
        tcgdex_set = TCGdexSet(
            id="swsh1",
            name="Sword & Shield",
            release_date=date(2020, 2, 7),
            series_id="swsh",
            series_name="Sword & Shield",
            logo="https://example.com/logo.png",
            symbol="https://example.com/symbol.png",
            card_count_total=216,
            card_count_official=202,
            legal_standard=False,
            legal_expanded=True,
            card_summaries=[],
        )
        db_set = tcgdex_set_to_db_set(tcgdex_set)
        assert db_set.id == "swsh1"
        assert db_set.name == "Sword & Shield"
        assert db_set.series == "Sword & Shield"
        assert db_set.release_date == date(2020, 2, 7)
        assert db_set.card_count == 202
        assert db_set.logo_url == "https://example.com/logo.png"
        assert db_set.legalities == {"standard": False, "expanded": True}

    def test_tcgdex_card_to_db_card(self):
        """Test converting TCGdex card to database card."""
        tcgdex_card = TCGdexCard(
            id="swsh1-1",
            local_id="1",
            name="Celebi V",
            supertype="Pokemon",
            subtypes=["V"],
            types=["Grass"],
            hp=180,
            stage="Basic",
            evolves_from=None,
            evolves_to=None,
            attacks=[{"name": "Find a Friend", "cost": ["Grass"]}],
            abilities=None,
            weaknesses=[{"type": "Fire", "value": "×2"}],
            resistances=None,
            retreat_cost=1,
            rules=None,
            set_id="swsh1",
            rarity="Holo Rare V",
            number="1",
            image_small="https://example.com/1.png",
            image_large="https://example.com/1/high.png",
            regulation_mark="D",
            legal_standard=False,
            legal_expanded=True,
        )
        db_card = tcgdex_card_to_db_card(tcgdex_card)
        assert db_card.id == "swsh1-1"
        assert db_card.local_id == "1"
        assert db_card.name == "Celebi V"
        assert db_card.supertype == "Pokemon"
        assert db_card.subtypes == ["V"]
        assert db_card.types == ["Grass"]
        assert db_card.hp == 180
        assert db_card.attacks == [{"name": "Find a Friend", "cost": ["Grass"]}]
        assert db_card.weaknesses == [{"type": "Fire", "value": "×2"}]
        assert db_card.retreat_cost == 1
        assert db_card.set_id == "swsh1"
        assert db_card.rarity == "Holo Rare V"
        assert db_card.regulation_mark == "D"
        assert db_card.legalities == {"standard": False, "expanded": True}


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_initial_state(self):
        """Test initial state of SyncResult."""
        result = SyncResult()
        assert result.sets_processed == 0
        assert result.sets_inserted == 0
        assert result.sets_updated == 0
        assert result.cards_processed == 0
        assert result.cards_inserted == 0
        assert result.cards_updated == 0
        assert result.errors == []


class TestCardSyncService:
    """Tests for CardSyncService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.begin = AsyncMock(return_value=AsyncMock())
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_tcgdex_client(self) -> AsyncMock:
        """Create mock TCGdex client."""
        return AsyncMock()

    @pytest.fixture
    def service(
        self, mock_session: AsyncMock, mock_tcgdex_client: AsyncMock
    ) -> CardSyncService:
        """Create CardSyncService for testing."""
        return CardSyncService(mock_session, mock_tcgdex_client)

    @pytest.mark.asyncio
    async def test_upsert_set_insert(
        self, service: CardSyncService, mock_session: AsyncMock
    ):
        """Test inserting a new set."""
        mock_session.get.return_value = None  # Set doesn't exist

        db_set = Set(id="swsh1", name="Sword & Shield", series="Sword & Shield")
        await service.upsert_set(db_set)

        mock_session.add.assert_called_once_with(db_set)
        assert service.result.sets_inserted == 1

    @pytest.mark.asyncio
    async def test_upsert_set_update(
        self, service: CardSyncService, mock_session: AsyncMock
    ):
        """Test updating an existing set."""
        existing_set = Set(id="swsh1", name="Old Name", series="Old Series")
        mock_session.get.return_value = existing_set

        new_set = Set(id="swsh1", name="Sword & Shield", series="Sword & Shield")
        await service.upsert_set(new_set)

        assert existing_set.name == "Sword & Shield"
        assert existing_set.series == "Sword & Shield"
        assert service.result.sets_updated == 1

    @pytest.mark.asyncio
    async def test_upsert_cards_batch(
        self, service: CardSyncService, mock_session: AsyncMock
    ):
        """Test batch upserting cards."""
        # Mock merge to return the same object
        mock_session.merge = AsyncMock(side_effect=lambda x: x)

        cards = [
            Card(
                id="swsh1-1",
                local_id="1",
                name="Card 1",
                supertype="Pokemon",
                set_id="swsh1",
            ),
            Card(
                id="swsh1-2",
                local_id="2",
                name="Card 2",
                supertype="Pokemon",
                set_id="swsh1",
            ),
        ]
        await service.upsert_cards(cards)

        assert mock_session.merge.call_count == 2
        assert service.result.cards_processed == 2

    @pytest.mark.asyncio
    async def test_sync_set_cards(
        self,
        service: CardSyncService,
        mock_session: AsyncMock,
        mock_tcgdex_client: AsyncMock,
    ):
        """Test syncing cards for a single set."""
        mock_session.get.return_value = None  # Set doesn't exist
        mock_session.merge = AsyncMock(side_effect=lambda x: x)

        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="swsh1",
            name="Sword & Shield",
            release_date=date(2020, 2, 7),
            series_id="swsh",
            series_name="Sword & Shield",
            logo=None,
            symbol=None,
            card_count_total=2,
            card_count_official=2,
            legal_standard=False,
            legal_expanded=True,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = [
            TCGdexCard(
                id="swsh1-1",
                local_id="1",
                name="Celebi V",
                supertype="Pokemon",
                subtypes=None,
                types=["Grass"],
                hp=180,
                stage="Basic",
                evolves_from=None,
                evolves_to=None,
                attacks=None,
                abilities=None,
                weaknesses=None,
                resistances=None,
                retreat_cost=1,
                rules=None,
                set_id="swsh1",
                rarity="Rare",
                number="1",
                image_small=None,
                image_large=None,
                regulation_mark="D",
                legal_standard=False,
                legal_expanded=True,
            )
        ]

        await service.sync_set("swsh1")

        assert service.result.sets_processed == 1
        assert service.result.sets_inserted == 1
        assert service.result.cards_processed == 1

    @pytest.mark.asyncio
    async def test_sync_all_english_sets(
        self,
        service: CardSyncService,
        mock_session: AsyncMock,
        mock_tcgdex_client: AsyncMock,
    ):
        """Test syncing all English sets."""
        mock_session.get.return_value = None
        mock_session.merge = AsyncMock(side_effect=lambda x: x)

        mock_tcgdex_client.fetch_all_sets.return_value = [
            TCGdexSetSummary(
                id="swsh1",
                name="Sword & Shield",
                logo=None,
                symbol=None,
                card_count_total=2,
                card_count_official=2,
            )
        ]
        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="swsh1",
            name="Sword & Shield",
            release_date=date(2020, 2, 7),
            series_id="swsh",
            series_name="Sword & Shield",
            logo=None,
            symbol=None,
            card_count_total=2,
            card_count_official=2,
            legal_standard=False,
            legal_expanded=True,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = []

        await service.sync_all_english()

        mock_tcgdex_client.fetch_all_sets.assert_called_once_with(language="en")
        assert service.result.sets_processed == 1

    @pytest.mark.asyncio
    async def test_update_japanese_names(
        self, service: CardSyncService, mock_session: AsyncMock
    ):
        """Test updating Japanese names from mapping."""
        # Mock existing card
        existing_card = Card(
            id="swsh1-1",
            local_id="1",
            name="Celebi V",
            supertype="Pokemon",
            set_id="swsh1",
            japanese_name=None,
        )
        mock_session.get.return_value = existing_card

        name_map = {"swsh1-1": "セレビィV"}
        await service.update_japanese_names(name_map)

        assert existing_card.japanese_name == "セレビィV"
