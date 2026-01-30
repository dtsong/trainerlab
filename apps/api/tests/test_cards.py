"""Tests for card endpoints and service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.card import Card
from src.models.meta_snapshot import MetaSnapshot
from src.schemas import CardResponse, CardUsageResponse, PaginatedResponse
from src.services.card_service import CardService, SortField, SortOrder
from src.services.usage_service import UsageService


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

    @pytest.mark.asyncio
    async def test_list_cards_with_set_id_filter(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by set_id."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(set_id="sv4")

        assert len(result.items) == 1
        assert result.items[0].set_id == "sv4"

    @pytest.mark.asyncio
    async def test_list_cards_with_standard_legality_filter(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by standard legality."""
        sample_card.legalities = {"standard": True}
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(standard=True)

        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_cards_with_expanded_legality_filter(
        self, service: CardService, sample_card: MagicMock
    ) -> None:
        """Test filtering by expanded legality."""
        sample_card.legalities = {"expanded": True}
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_card]
        service.session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            mock_result,
        ]

        result = await service.list_cards(expanded=True)

        assert len(result.items) == 1

    @pytest.fixture
    def full_card(self) -> MagicMock:
        """Create a full card mock with all fields."""
        from datetime import datetime

        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.local_id = "6"
        card.name = "Pikachu"
        card.japanese_name = "ピカチュウ"
        card.supertype = "Pokemon"
        card.subtypes = ["Basic"]
        card.types = ["Lightning"]
        card.hp = 60
        card.stage = None
        card.evolves_from = None
        card.evolves_to = ["Raichu"]
        card.attacks = [{"name": "Thunderbolt", "cost": ["L", "C"], "damage": "50"}]
        card.abilities = None
        card.weaknesses = [{"type": "Fighting", "value": "×2"}]
        card.resistances = None
        card.retreat_cost = 1
        card.rules = None
        card.set_id = "sv4"
        card.rarity = "Common"
        card.number = "6"
        card.image_small = "https://example.com/pikachu_small.png"
        card.image_large = "https://example.com/pikachu_large.png"
        card.regulation_mark = "G"
        card.legalities = {"standard": True, "expanded": True}
        card.created_at = datetime(2024, 1, 1, 0, 0, 0)
        card.updated_at = datetime(2024, 1, 1, 0, 0, 0)
        card.set = None
        return card

    @pytest.mark.asyncio
    async def test_get_card_by_id(
        self, service: CardService, full_card: MagicMock
    ) -> None:
        """Test getting a card by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = full_card
        service.session.execute.return_value = mock_result

        result = await service.get_card("sv4-6")

        assert result is not None
        assert isinstance(result, CardResponse)
        assert result.id == "sv4-6"
        assert result.name == "Pikachu"

    @pytest.mark.asyncio
    async def test_get_card_not_found(self, service: CardService) -> None:
        """Test getting a card that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute.return_value = mock_result

        result = await service.get_card("nonexistent")

        assert result is None


class TestUsageService:
    """Tests for UsageService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> UsageService:
        """Create a UsageService with mock session."""
        return UsageService(mock_session)

    @pytest.fixture
    def sample_snapshot(self) -> MagicMock:
        """Create a sample meta snapshot mock."""
        from datetime import date

        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.format = "standard"
        snapshot.sample_size = 100
        snapshot.card_usage = {"sv4-6": {"inclusion_rate": 0.85, "avg_copies": 3.5}}
        return snapshot

    @pytest.mark.asyncio
    async def test_get_card_usage_with_data(
        self, service: UsageService, sample_snapshot: MagicMock
    ) -> None:
        """Test getting card usage when data exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_snapshot]
        service.session.execute.return_value = mock_result

        result = await service.get_card_usage("sv4-6", format="standard", days=30)

        assert result is not None
        assert isinstance(result, CardUsageResponse)
        assert result.card_id == "sv4-6"
        assert result.inclusion_rate == 0.85
        assert result.avg_copies == 3.5
        assert result.sample_size == 100

    @pytest.mark.asyncio
    async def test_get_card_usage_no_snapshots(self, service: UsageService) -> None:
        """Test getting card usage when no snapshots exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        result = await service.get_card_usage("sv4-6")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_card_usage_card_not_in_usage(
        self, service: UsageService, sample_snapshot: MagicMock
    ) -> None:
        """Test getting usage for card not in snapshot data."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_snapshot]
        service.session.execute.return_value = mock_result

        result = await service.get_card_usage("nonexistent", format="standard")

        assert result is not None
        assert result.inclusion_rate == 0.0
        assert result.avg_copies is None


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

    def test_list_cards_with_set_id_filter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that set_id filter parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?set_id=sv4")

        assert response.status_code == 200

    def test_list_cards_with_standard_filter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that standard legality filter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?standard=true")

        assert response.status_code == 200

    def test_list_cards_with_expanded_filter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that expanded legality filter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get("/api/v1/cards?expanded=true")

        assert response.status_code == 200

    def test_list_cards_combined_filters(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that all filters can be combined."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            mock_result,
        ]

        response = client.get(
            "/api/v1/cards?q=pikachu&supertype=Pokemon&types=Lightning&set_id=sv4&standard=true"
        )

        assert response.status_code == 200

    def test_get_card_by_id(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test getting a card by ID returns 200."""
        from datetime import datetime

        mock_card = MagicMock(spec=Card)
        mock_card.id = "sv4-6"
        mock_card.local_id = "6"
        mock_card.name = "Pikachu"
        mock_card.japanese_name = None
        mock_card.supertype = "Pokemon"
        mock_card.subtypes = ["Basic"]
        mock_card.types = ["Lightning"]
        mock_card.hp = 60
        mock_card.stage = None
        mock_card.evolves_from = None
        mock_card.evolves_to = None
        mock_card.attacks = None
        mock_card.abilities = None
        mock_card.weaknesses = None
        mock_card.resistances = None
        mock_card.retreat_cost = 1
        mock_card.rules = None
        mock_card.set_id = "sv4"
        mock_card.rarity = "Common"
        mock_card.number = "6"
        mock_card.image_small = "https://example.com/small.png"
        mock_card.image_large = "https://example.com/large.png"
        mock_card.regulation_mark = "G"
        mock_card.legalities = {"standard": True}
        mock_card.created_at = datetime(2024, 1, 1)
        mock_card.updated_at = datetime(2024, 1, 1)
        mock_card.set = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_card
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/sv4-6")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sv4-6"
        assert data["name"] == "Pikachu"

    def test_get_card_not_found(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test getting a non-existent card returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Card not found"

    def test_get_card_usage_card_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test getting usage for non-existent card returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/nonexistent/usage")

        assert response.status_code == 404

    def test_get_card_usage_returns_data(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test getting usage for existing card returns data."""
        from datetime import date, datetime

        # Mock card exists
        mock_card = MagicMock(spec=Card)
        mock_card.id = "sv4-6"
        mock_card.local_id = "6"
        mock_card.name = "Pikachu"
        mock_card.japanese_name = None
        mock_card.supertype = "Pokemon"
        mock_card.subtypes = None
        mock_card.types = ["Lightning"]
        mock_card.hp = 60
        mock_card.stage = None
        mock_card.evolves_from = None
        mock_card.evolves_to = None
        mock_card.attacks = None
        mock_card.abilities = None
        mock_card.weaknesses = None
        mock_card.resistances = None
        mock_card.retreat_cost = 1
        mock_card.rules = None
        mock_card.set_id = "sv4"
        mock_card.rarity = "Common"
        mock_card.number = "6"
        mock_card.image_small = None
        mock_card.image_large = None
        mock_card.regulation_mark = None
        mock_card.legalities = None
        mock_card.created_at = datetime(2024, 1, 1)
        mock_card.updated_at = datetime(2024, 1, 1)
        mock_card.set = None

        # Mock snapshot
        mock_snapshot = MagicMock(spec=MetaSnapshot)
        mock_snapshot.snapshot_date = date(2024, 1, 15)
        mock_snapshot.format = "standard"
        mock_snapshot.sample_size = 100
        mock_snapshot.card_usage = {
            "sv4-6": {"inclusion_rate": 0.85, "avg_copies": 3.5}
        }

        # First call: card lookup, second call: usage lookup
        card_result = MagicMock()
        card_result.scalar_one_or_none.return_value = mock_card
        usage_result = MagicMock()
        usage_result.scalars.return_value.all.return_value = [mock_snapshot]
        mock_db.execute.side_effect = [card_result, usage_result]

        response = client.get("/api/v1/cards/sv4-6/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == "sv4-6"
        assert data["inclusion_rate"] == 0.85
        assert data["avg_copies"] == 3.5

    def test_get_card_usage_no_meta_data(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test getting usage when no meta snapshots exist returns zeros."""
        from datetime import datetime

        # Mock card exists
        mock_card = MagicMock(spec=Card)
        mock_card.id = "sv4-6"
        mock_card.local_id = "6"
        mock_card.name = "Pikachu"
        mock_card.japanese_name = None
        mock_card.supertype = "Pokemon"
        mock_card.subtypes = None
        mock_card.types = ["Lightning"]
        mock_card.hp = 60
        mock_card.stage = None
        mock_card.evolves_from = None
        mock_card.evolves_to = None
        mock_card.attacks = None
        mock_card.abilities = None
        mock_card.weaknesses = None
        mock_card.resistances = None
        mock_card.retreat_cost = 1
        mock_card.rules = None
        mock_card.set_id = "sv4"
        mock_card.rarity = "Common"
        mock_card.number = "6"
        mock_card.image_small = None
        mock_card.image_large = None
        mock_card.regulation_mark = None
        mock_card.legalities = None
        mock_card.created_at = datetime(2024, 1, 1)
        mock_card.updated_at = datetime(2024, 1, 1)
        mock_card.set = None

        # First call: card lookup, second call: empty usage
        card_result = MagicMock()
        card_result.scalar_one_or_none.return_value = mock_card
        usage_result = MagicMock()
        usage_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [card_result, usage_result]

        response = client.get("/api/v1/cards/sv4-6/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == "sv4-6"
        assert data["inclusion_rate"] == 0.0
        assert data["sample_size"] == 0
