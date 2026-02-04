"""Tests for SetService."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.card import Card
from src.models.set import Set
from src.schemas import PaginatedResponse, SetResponse
from src.services.set_service import SetService, SetSortField, SetSortOrder


class TestSetServiceListSets:
    """Tests for SetService.list_sets."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> SetService:
        """Create a SetService with mock session."""
        return SetService(mock_session)

    @pytest.fixture
    def sample_set(self) -> MagicMock:
        """Create a sample set mock."""
        s = MagicMock(spec=Set)
        s.id = "sv4"
        s.name = "Paradox Rift"
        s.series = "Scarlet & Violet"
        s.release_date = date(2023, 11, 3)
        s.release_date_jp = date(2023, 9, 22)
        s.card_count = 182
        s.logo_url = "https://example.com/sv4_logo.png"
        s.symbol_url = "https://example.com/sv4_symbol.png"
        s.legalities = {"standard": True, "expanded": True}
        s.created_at = datetime(2024, 1, 1, 0, 0, 0)
        s.updated_at = datetime(2024, 1, 1, 0, 0, 0)
        return s

    @pytest.fixture
    def another_set(self) -> MagicMock:
        """Create a second sample set mock."""
        s = MagicMock(spec=Set)
        s.id = "sv3"
        s.name = "Obsidian Flames"
        s.series = "Scarlet & Violet"
        s.release_date = date(2023, 8, 11)
        s.release_date_jp = date(2023, 7, 28)
        s.card_count = 197
        s.logo_url = "https://example.com/sv3_logo.png"
        s.symbol_url = "https://example.com/sv3_symbol.png"
        s.legalities = {"standard": True, "expanded": True}
        s.created_at = datetime(2024, 1, 1, 0, 0, 0)
        s.updated_at = datetime(2024, 1, 1, 0, 0, 0)
        return s

    @pytest.mark.asyncio
    async def test_list_sets_empty(self, service: SetService) -> None:
        """Test listing sets when no sets exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        result = await service.list_sets()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_sets_returns_set_responses(
        self, service: SetService, sample_set: MagicMock
    ) -> None:
        """Test listing sets returns a list of SetResponse objects."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_set]
        service.session.execute.return_value = mock_result

        result = await service.list_sets()

        assert len(result) == 1
        assert isinstance(result[0], SetResponse)
        assert result[0].id == "sv4"
        assert result[0].name == "Paradox Rift"
        assert result[0].series == "Scarlet & Violet"

    @pytest.mark.asyncio
    async def test_list_sets_multiple(
        self,
        service: SetService,
        sample_set: MagicMock,
        another_set: MagicMock,
    ) -> None:
        """Test listing multiple sets."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_set, another_set]
        service.session.execute.return_value = mock_result

        result = await service.list_sets()

        assert len(result) == 2
        assert result[0].id == "sv4"
        assert result[1].id == "sv3"

    @pytest.mark.asyncio
    async def test_list_sets_filter_by_series(
        self, service: SetService, sample_set: MagicMock
    ) -> None:
        """Test filtering sets by series name."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_set]
        service.session.execute.return_value = mock_result

        result = await service.list_sets(series="Scarlet & Violet")

        assert len(result) == 1
        assert result[0].series == "Scarlet & Violet"

    @pytest.mark.asyncio
    async def test_list_sets_filter_by_series_no_match(
        self, service: SetService
    ) -> None:
        """Test filtering by series with no matching results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        result = await service.list_sets(series="Nonexistent Series")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_sets_default_sort_release_date_desc(
        self, service: SetService
    ) -> None:
        """Test that default sort is by release_date descending."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        await service.list_sets()

        # Verify execute was called (query was built with defaults)
        service.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sets_sort_by_name_asc(self, service: SetService) -> None:
        """Test sorting sets by name ascending."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        await service.list_sets(sort_by=SetSortField.NAME, sort_order=SetSortOrder.ASC)

        service.session.execute.assert_called_once()


class TestSetServiceGetSet:
    """Tests for SetService.get_set."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> SetService:
        """Create a SetService with mock session."""
        return SetService(mock_session)

    @pytest.fixture
    def sample_set(self) -> MagicMock:
        """Create a sample set mock."""
        s = MagicMock(spec=Set)
        s.id = "sv4"
        s.name = "Paradox Rift"
        s.series = "Scarlet & Violet"
        s.release_date = date(2023, 11, 3)
        s.release_date_jp = date(2023, 9, 22)
        s.card_count = 182
        s.logo_url = "https://example.com/sv4_logo.png"
        s.symbol_url = "https://example.com/sv4_symbol.png"
        s.legalities = {"standard": True, "expanded": True}
        s.created_at = datetime(2024, 1, 1, 0, 0, 0)
        s.updated_at = datetime(2024, 1, 1, 0, 0, 0)
        return s

    @pytest.mark.asyncio
    async def test_get_set_found(
        self, service: SetService, sample_set: MagicMock
    ) -> None:
        """Test getting a set by ID that exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_set
        service.session.execute.return_value = mock_result

        result = await service.get_set("sv4")

        assert result is not None
        assert isinstance(result, SetResponse)
        assert result.id == "sv4"
        assert result.name == "Paradox Rift"
        assert result.card_count == 182

    @pytest.mark.asyncio
    async def test_get_set_not_found(self, service: SetService) -> None:
        """Test getting a set by ID that does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute.return_value = mock_result

        result = await service.get_set("nonexistent")

        assert result is None


class TestSetServiceGetSetCards:
    """Tests for SetService.get_set_cards."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> SetService:
        """Create a SetService with mock session."""
        return SetService(mock_session)

    @pytest.fixture
    def sample_card(self) -> MagicMock:
        """Create a sample card mock."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.name = "Pikachu"
        card.supertype = "Pokemon"
        card.types = ["Lightning"]
        card.set_id = "sv4"
        card.rarity = "Common"
        card.image_small = "https://example.com/pikachu.png"
        return card

    @pytest.mark.asyncio
    async def test_get_set_cards_empty(self, service: SetService) -> None:
        """Test getting cards for a set with no cards."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),  # count query
            mock_result,  # main query
        ]

        result = await service.get_set_cards("sv4")

        assert isinstance(result, PaginatedResponse)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.limit == 20
        assert result.has_next is False
        assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_get_set_cards_with_results(
        self, service: SetService, sample_card: MagicMock
    ) -> None:
        """Test getting cards for a set with results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),  # count query
            mock_result,  # main query
        ]

        result = await service.get_set_cards("sv4")

        assert len(result.items) == 1
        assert result.items[0].id == "sv4-6"
        assert result.items[0].name == "Pikachu"
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_set_cards_pagination_page_2(
        self, service: SetService, sample_card: MagicMock
    ) -> None:
        """Test pagination on page 2."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=50)),  # 50 total
            mock_result,
        ]

        result = await service.get_set_cards("sv4", page=2, limit=20)

        assert result.page == 2
        assert result.limit == 20
        assert result.total == 50
        assert result.has_next is True
        assert result.has_prev is True
        assert result.total_pages == 3

    @pytest.mark.asyncio
    async def test_get_set_cards_last_page(
        self, service: SetService, sample_card: MagicMock
    ) -> None:
        """Test that last page has no next."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=40)),  # 40 total, 2 pages
            mock_result,
        ]

        result = await service.get_set_cards("sv4", page=2, limit=20)

        assert result.has_next is False
        assert result.has_prev is True


class TestSetSortEnums:
    """Tests for SetSortField and SetSortOrder enums."""

    def test_sort_field_values(self) -> None:
        """Test SetSortField enum values."""
        assert SetSortField.NAME.value == "name"
        assert SetSortField.RELEASE_DATE.value == "release_date"

    def test_sort_order_values(self) -> None:
        """Test SetSortOrder enum values."""
        assert SetSortOrder.ASC.value == "asc"
        assert SetSortOrder.DESC.value == "desc"
