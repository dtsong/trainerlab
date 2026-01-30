"""Tests for card endpoints and service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.card import Card
from src.schemas import PaginatedResponse
from src.services.card_service import CardService, SortField, SortOrder


class TestCardService:
    """Tests for CardService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> CardService:
        """Create a CardService with mock session."""
        return CardService(mock_session)

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
    async def test_list_cards_empty(self, service: CardService) -> None:
        """Test listing cards when no cards exist."""
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),  # count query
            mock_result,  # main query
        ]

        result = await service.list_cards()

        assert isinstance(result, PaginatedResponse)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.limit == 20
        assert result.has_next is False
        assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_list_cards_with_results(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test listing cards with results."""
        # Mock results with one card
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),  # count query
            mock_result,  # main query
        ]

        result = await service.list_cards()

        assert len(result.items) == 1
        assert result.items[0].id == "sv4-6"
        assert result.items[0].name == "Pikachu"
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_cards_pagination(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test pagination calculations."""
        # Mock results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=100)),  # total count
            mock_result,
        ]

        result = await service.list_cards(page=2, limit=20)

        assert result.page == 2
        assert result.limit == 20
        assert result.total == 100
        assert result.has_next is True
        assert result.has_prev is True
        assert result.total_pages == 5

    @pytest.mark.asyncio
    async def test_list_cards_last_page(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test last page has no next."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=41)),  # 41 total, 3 pages
            mock_result,
        ]

        result = await service.list_cards(page=3, limit=20)

        assert result.has_next is False
        assert result.has_prev is True

    @pytest.mark.asyncio
    async def test_list_cards_with_search_query(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test search query parameter is passed to query."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(q="pikachu")

        assert len(result.items) == 1
        assert result.items[0].name == "Pikachu"

    @pytest.mark.asyncio
    async def test_list_cards_search_returns_empty(self, service: CardService) -> None:
        """Test search query with no matching results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        result = await service.list_cards(q="nonexistent")

        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_cards_with_supertype_filter(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by single supertype."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(supertype=["Pokemon"])

        assert len(result.items) == 1
        assert result.items[0].supertype == "Pokemon"

    @pytest.mark.asyncio
    async def test_list_cards_with_multiple_supertypes(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by multiple supertypes."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(supertype=["Pokemon", "Trainer"])

        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_cards_with_types_filter(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by single Pokemon type."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(types=["Lightning"])

        assert len(result.items) == 1
        assert result.items[0].types == ["Lightning"]

    @pytest.mark.asyncio
    async def test_list_cards_with_multiple_types(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by multiple Pokemon types."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(types=["Fire", "Water"])

        assert len(result.items) == 1


class TestSortEnums:
    """Tests for sort enums."""

    def test_sort_field_values(self) -> None:
        """Test SortField enum values."""
        assert SortField.NAME.value == "name"
        assert SortField.SET.value == "set_id"
        assert SortField.DATE.value == "created_at"

    def test_sort_order_values(self) -> None:
        """Test SortOrder enum values."""
        assert SortOrder.ASC.value == "asc"
        assert SortOrder.DESC.value == "desc"


class TestCardsEndpoint:
    """Tests for cards API endpoint."""

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

    def test_list_cards_endpoint_exists(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that the cards endpoint exists."""
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),  # count query
            mock_result,  # main query
        ]

        response = client.get("/api/v1/cards")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20

    def test_list_cards_invalid_page(self, client: TestClient) -> None:
        """Test that page < 1 returns 422."""
        response = client.get("/api/v1/cards?page=0")
        assert response.status_code == 422

    def test_list_cards_invalid_limit(self, client: TestClient) -> None:
        """Test that limit > 100 returns 422."""
        response = client.get("/api/v1/cards?limit=101")
        assert response.status_code == 422

    def test_list_cards_invalid_limit_zero(self, client: TestClient) -> None:
        """Test that limit < 1 returns 422."""
        response = client.get("/api/v1/cards?limit=0")
        assert response.status_code == 422

    def test_list_cards_with_search_query(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that search query parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?q=pikachu")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_list_cards_with_supertype_filter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that supertype filter parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?supertype=Pokemon")

        assert response.status_code == 200

    def test_list_cards_with_multiple_supertypes(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that multiple supertype values are accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?supertype=Pokemon&supertype=Trainer")

        assert response.status_code == 200

    def test_list_cards_with_types_filter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that types filter parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?types=Fire")

        assert response.status_code == 200

    def test_list_cards_with_multiple_types(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that multiple types values are accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?types=Fire&types=Water")

        assert response.status_code == 200
