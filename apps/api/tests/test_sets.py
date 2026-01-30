"""Tests for sets endpoints and service."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.card import Card
from src.models.set import Set
from src.schemas import PaginatedResponse, SetResponse
from src.services.set_service import SetService, SetSortField, SetSortOrder


class TestSetService:
    """Tests for SetService."""

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
        set_obj = MagicMock(spec=Set)
        set_obj.id = "sv4"
        set_obj.name = "Paradox Rift"
        set_obj.series = "Scarlet & Violet"
        set_obj.release_date = date(2023, 11, 3)
        set_obj.release_date_jp = date(2023, 9, 22)
        set_obj.card_count = 266
        set_obj.logo_url = "https://example.com/logo.png"
        set_obj.symbol_url = "https://example.com/symbol.png"
        set_obj.legalities = {"standard": "Legal", "expanded": "Legal"}
        set_obj.created_at = datetime(2024, 1, 1)
        set_obj.updated_at = datetime(2024, 1, 1)
        return set_obj

    @pytest.mark.asyncio
    async def test_list_sets_empty(self, service: SetService) -> None:
        """Test listing sets when none exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        result = await service.list_sets()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_sets_with_results(
        self, service: SetService, sample_set: MagicMock
    ) -> None:
        """Test listing sets with results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_set]
        service.session.execute.return_value = mock_result

        result = await service.list_sets()

        assert len(result) == 1
        assert result[0].id == "sv4"
        assert result[0].name == "Paradox Rift"

    @pytest.mark.asyncio
    async def test_list_sets_with_series_filter(
        self, service: SetService, sample_set: MagicMock
    ) -> None:
        """Test filtering sets by series."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_set]
        service.session.execute.return_value = mock_result

        result = await service.list_sets(series="Scarlet & Violet")

        assert len(result) == 1
        assert result[0].series == "Scarlet & Violet"

    @pytest.mark.asyncio
    async def test_get_set_by_id(
        self, service: SetService, sample_set: MagicMock
    ) -> None:
        """Test getting a set by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_set
        service.session.execute.return_value = mock_result

        result = await service.get_set("sv4")

        assert result is not None
        assert isinstance(result, SetResponse)
        assert result.id == "sv4"

    @pytest.mark.asyncio
    async def test_get_set_not_found(self, service: SetService) -> None:
        """Test getting a set that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute.return_value = mock_result

        result = await service.get_set("nonexistent")

        assert result is None

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
    async def test_get_set_cards(
        self, service: SetService, sample_card: MagicMock
    ) -> None:
        """Test getting cards for a set."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        mock_cards_result = MagicMock()
        mock_cards_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [mock_count_result, mock_cards_result]

        result = await service.get_set_cards("sv4")

        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 1
        assert result.items[0].id == "sv4-6"

    @pytest.mark.asyncio
    async def test_get_set_cards_empty(self, service: SetService) -> None:
        """Test getting cards for a set with no cards."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_cards_result = MagicMock()
        mock_cards_result.scalars.return_value.all.return_value = []
        service.session.execute.side_effect = [mock_count_result, mock_cards_result]

        result = await service.get_set_cards("sv4")

        assert result.items == []
        assert result.total == 0


class TestSortEnums:
    """Tests for sort enums."""

    def test_set_sort_field_values(self) -> None:
        """Test SetSortField enum values."""
        assert SetSortField.NAME.value == "name"
        assert SetSortField.RELEASE_DATE.value == "release_date"

    def test_set_sort_order_values(self) -> None:
        """Test SetSortOrder enum values."""
        assert SetSortOrder.ASC.value == "asc"
        assert SetSortOrder.DESC.value == "desc"


class TestSetsEndpoint:
    """Tests for sets API endpoint."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""
        from src.db.database import get_db

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_list_sets_endpoint_exists(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that the sets endpoint exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/sets")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_sets_with_series_filter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test filtering sets by series."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/sets?series=Scarlet%20%26%20Violet")

        assert response.status_code == 200

    def test_get_set_by_id(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test getting a set by ID returns 200."""
        mock_set = MagicMock(spec=Set)
        mock_set.id = "sv4"
        mock_set.name = "Paradox Rift"
        mock_set.series = "Scarlet & Violet"
        mock_set.release_date = date(2023, 11, 3)
        mock_set.release_date_jp = None
        mock_set.card_count = 266
        mock_set.logo_url = None
        mock_set.symbol_url = None
        mock_set.legalities = None
        mock_set.created_at = datetime(2024, 1, 1)
        mock_set.updated_at = datetime(2024, 1, 1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_set
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/sets/sv4")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sv4"
        assert data["name"] == "Paradox Rift"

    def test_get_set_not_found(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test getting a non-existent set returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/sets/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Set not found"

    def test_get_set_cards(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test getting cards for a set."""
        # Mock set exists
        mock_set = MagicMock(spec=Set)
        mock_set.id = "sv4"
        mock_set.name = "Paradox Rift"
        mock_set.series = "Scarlet & Violet"
        mock_set.release_date = None
        mock_set.release_date_jp = None
        mock_set.card_count = 266
        mock_set.logo_url = None
        mock_set.symbol_url = None
        mock_set.legalities = None
        mock_set.created_at = datetime(2024, 1, 1)
        mock_set.updated_at = datetime(2024, 1, 1)

        # Mock card
        mock_card = MagicMock(spec=Card)
        mock_card.id = "sv4-6"
        mock_card.name = "Pikachu"
        mock_card.supertype = "Pokemon"
        mock_card.types = ["Lightning"]
        mock_card.set_id = "sv4"
        mock_card.rarity = "Common"
        mock_card.image_small = None

        # First call: set lookup, second: count, third: cards
        set_result = MagicMock()
        set_result.scalar_one_or_none.return_value = mock_set
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        cards_result = MagicMock()
        cards_result.scalars.return_value.all.return_value = [mock_card]
        mock_db.execute.side_effect = [set_result, count_result, cards_result]

        response = client.get("/api/v1/sets/sv4/cards")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "sv4-6"
        assert data["total"] == 1

    def test_get_set_cards_set_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test getting cards for non-existent set returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/sets/nonexistent/cards")

        assert response.status_code == 404
        assert response.json()["detail"] == "Set not found"
