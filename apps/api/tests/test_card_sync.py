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
    normalize_jp_card_id,
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


class TestNormalizeJpCardId:
    """Tests for normalize_jp_card_id."""

    def test_sv9_zero_strip(self):
        """SV9-097 -> sv09-97."""
        assert normalize_jp_card_id("SV9-097", "SV9") == "sv09-97"

    def test_sv6a_mapping(self):
        """SV6a-042 -> sv6pt5-42."""
        result = normalize_jp_card_id("SV6a-042", "SV6a")
        assert result == "sv6pt5-42"

    def test_single_digit(self):
        """SV9-003 -> sv09-3."""
        assert normalize_jp_card_id("SV9-003", "SV9") == "sv09-3"

    def test_no_leading_zeros(self):
        """SV8-12 -> sv08-12 (no zeros to strip)."""
        result = normalize_jp_card_id("SV8-12", "SV8")
        assert result == "sv08-12"

    def test_unknown_set_returns_none(self):
        """Unknown set ID returns None."""
        assert normalize_jp_card_id("XY1-001", "XY1") is None

    def test_me_sets_not_mapped(self):
        """ME block sets excluded (synced via EN pipeline)."""
        assert normalize_jp_card_id("SVME1-010", "SVME1") is None
        assert normalize_jp_card_id("SVMEE-007", "SVMEE") is None


class TestSyncJpSet:
    """Tests for CardSyncService.sync_jp_set."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def mock_tcgdex_client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(
        self, mock_session: AsyncMock, mock_tcgdex_client: AsyncMock
    ) -> CardSyncService:
        return CardSyncService(mock_session, mock_tcgdex_client)

    @pytest.mark.asyncio
    async def test_inserts_new_jp_card(
        self,
        service: CardSyncService,
        mock_session: AsyncMock,
        mock_tcgdex_client: AsyncMock,
    ):
        """New JP-only card is inserted with Limitless-normalized ID."""
        mock_session.get.return_value = None  # No existing set or card

        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="SV9",
            name="超電ブレイカー",
            release_date=date(2024, 12, 6),
            series_id="sv",
            series_name="Scarlet & Violet",
            logo=None,
            symbol=None,
            card_count_total=100,
            card_count_official=97,
            legal_standard=None,
            legal_expanded=None,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = [
            TCGdexCard(
                id="SV9-097",
                local_id="097",
                name="ゾロアークex",
                supertype="Pokemon",
                subtypes=["ex"],
                types=["Darkness"],
                hp=270,
                stage="Stage 1",
                evolves_from="ゾロア",
                evolves_to=None,
                attacks=None,
                abilities=None,
                weaknesses=None,
                resistances=None,
                retreat_cost=2,
                rules=None,
                set_id="SV9",
                rarity="RR",
                number="097",
                image_small="https://assets.tcgdex.net/ja/sv/sv9/097",
                image_large="https://assets.tcgdex.net/ja/sv/sv9/097/high",
                regulation_mark="H",
                legal_standard=None,
                legal_expanded=None,
            )
        ]

        await service.sync_jp_set("SV9")

        # Card should be added with normalized ID
        added_card = mock_session.add.call_args_list[-1][0][0]
        assert isinstance(added_card, Card)
        assert added_card.id == "sv09-97"
        assert added_card.name == "ゾロアークex"
        assert added_card.japanese_name == "ゾロアークex"
        assert added_card.set_id == "sv09"
        assert added_card.image_small == ("https://assets.tcgdex.net/ja/sv/sv9/097")
        assert service.result.cards_inserted == 1

    @pytest.mark.asyncio
    async def test_skips_existing_en_card(
        self,
        service: CardSyncService,
        mock_session: AsyncMock,
        mock_tcgdex_client: AsyncMock,
    ):
        """Existing EN card is not overwritten, only japanese_name backfilled."""
        existing_card = Card(
            id="sv7-50",
            local_id="50",
            name="Charizard ex",
            supertype="Pokemon",
            set_id="sv7",
            japanese_name=None,
            image_small="https://assets.tcgdex.net/en/sv/sv7/050",
        )

        # First call for Set, second for Card
        mock_session.get.side_effect = [None, existing_card]

        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="SV7",
            name="ステラミラクル",
            release_date=date(2024, 7, 19),
            series_id="sv",
            series_name="Scarlet & Violet",
            logo=None,
            symbol=None,
            card_count_total=2,
            card_count_official=2,
            legal_standard=None,
            legal_expanded=None,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = [
            TCGdexCard(
                id="SV7-050",
                local_id="050",
                name="リザードンex",
                supertype="Pokemon",
                subtypes=None,
                types=["Fire"],
                hp=330,
                stage="Stage 2",
                evolves_from=None,
                evolves_to=None,
                attacks=None,
                abilities=None,
                weaknesses=None,
                resistances=None,
                retreat_cost=3,
                rules=None,
                set_id="SV7",
                rarity="RR",
                number="050",
                image_small="https://assets.tcgdex.net/ja/sv/sv7/050",
                image_large=None,
                regulation_mark="H",
                legal_standard=None,
                legal_expanded=None,
            )
        ]

        await service.sync_jp_set("SV7")

        # Name/image should NOT be overwritten
        assert existing_card.name == "Charizard ex"
        assert existing_card.image_small == ("https://assets.tcgdex.net/en/sv/sv7/050")
        # But japanese_name should be backfilled
        assert existing_card.japanese_name == "リザードンex"
        assert service.result.cards_updated == 1
        assert service.result.cards_inserted == 0

    @pytest.mark.asyncio
    async def test_unknown_set_records_error(
        self,
        service: CardSyncService,
    ):
        """Unknown set ID records an error."""
        await service.sync_jp_set("UNKNOWN_SET")

        assert len(service.result.errors) == 1
        assert "Unknown JP set" in service.result.errors[0]

    @pytest.mark.asyncio
    async def test_tcgdex_error_handled(
        self,
        service: CardSyncService,
        mock_tcgdex_client: AsyncMock,
    ):
        """TCGdex API error is caught and recorded."""
        from src.clients.tcgdex import TCGdexError

        mock_tcgdex_client.fetch_set.side_effect = TCGdexError("Not found")

        await service.sync_jp_set("SV9")

        assert len(service.result.errors) == 1
        assert "Error syncing JP set SV9" in service.result.errors[0]
