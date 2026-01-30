"""Tests for deck endpoints and service."""

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.deck import Deck
from src.models.user import User
from src.schemas import DeckCreate, PaginatedResponse
from src.services.deck_service import DeckService


class TestDeckService:
    """Tests for DeckService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckService:
        """Create a DeckService with mock session."""
        return DeckService(mock_session)

    @pytest.fixture
    def sample_user(self) -> MagicMock:
        """Create a sample user mock."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        return user

    @pytest.fixture
    def sample_deck(self, sample_user: MagicMock) -> MagicMock:
        """Create a sample deck mock."""
        from datetime import datetime

        deck = MagicMock(spec=Deck)
        deck.id = uuid4()
        deck.user_id = sample_user.id
        deck.name = "Test Deck"
        deck.description = "A test deck"
        deck.cards = [{"card_id": "sv4-6", "quantity": 4}]
        deck.format = "standard"
        deck.archetype = None
        deck.is_public = False
        deck.share_code = None
        deck.created_at = datetime.now(UTC)
        deck.updated_at = datetime.now(UTC)
        deck.user = sample_user
        return deck

    @pytest.mark.asyncio
    async def test_create_deck_success(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test creating a deck successfully."""
        from datetime import datetime

        deck_data = DeckCreate(
            name="My New Deck",
            description="A cool deck",
            cards=[],
            format="standard",
            is_public=False,
        )

        # Mock the session operations
        service.session.add = MagicMock()
        service.session.commit = AsyncMock()

        # Mock refresh to set server-side defaults
        async def mock_refresh(obj, attrs=None):
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        service.session.refresh = AsyncMock(side_effect=mock_refresh)

        result = await service.create_deck(sample_user, deck_data)

        assert result.name == "My New Deck"
        assert result.description == "A cool deck"
        assert result.format == "standard"
        assert result.is_public is False
        service.session.add.assert_called_once()
        service.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_deck_with_cards_validates(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test that card IDs are validated when creating a deck."""
        from datetime import datetime

        from src.schemas import CardInDeck

        deck_data = DeckCreate(
            name="Deck with Cards",
            cards=[CardInDeck(card_id="sv4-6", quantity=4)],
            format="standard",
            is_public=False,
        )

        # Mock card validation - cards exist
        mock_result = MagicMock()
        mock_result.all.return_value = [("sv4-6",)]
        service.session.execute = AsyncMock(return_value=mock_result)
        service.session.add = MagicMock()
        service.session.commit = AsyncMock()

        # Mock refresh to set server-side defaults
        async def mock_refresh(obj, attrs=None):
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        service.session.refresh = AsyncMock(side_effect=mock_refresh)

        result = await service.create_deck(sample_user, deck_data)

        assert result.name == "Deck with Cards"
        assert len(result.cards) == 1
        assert result.cards[0].card_id == "sv4-6"

    @pytest.mark.asyncio
    async def test_create_deck_invalid_card_raises(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test that invalid card IDs raise ValueError."""
        from src.schemas import CardInDeck

        deck_data = DeckCreate(
            name="Invalid Deck",
            cards=[CardInDeck(card_id="nonexistent-card", quantity=4)],
            format="standard",
            is_public=False,
        )

        # Mock card validation - cards don't exist
        mock_result = MagicMock()
        mock_result.all.return_value = []
        service.session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="Card IDs not found"):
            await service.create_deck(sample_user, deck_data)

    @pytest.mark.asyncio
    async def test_list_user_decks_empty(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test listing decks when user has none."""
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=0)),  # count query
                mock_result,  # main query
            ]
        )

        result = await service.list_user_decks(sample_user)

        assert isinstance(result, PaginatedResponse)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.has_next is False
        assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_list_user_decks_with_results(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test listing decks with results."""
        # Mock results with one deck
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # count query
                mock_result,  # main query
            ]
        )

        result = await service.list_user_decks(sample_user)

        assert len(result.items) == 1
        assert result.items[0].name == "Test Deck"
        assert result.items[0].card_count == 4  # 1 card with quantity 4
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_user_decks_pagination(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test pagination calculations for deck listing."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=50)),  # total count
                mock_result,
            ]
        )

        result = await service.list_user_decks(sample_user, page=2, limit=20)

        assert result.page == 2
        assert result.limit == 20
        assert result.total == 50
        assert result.has_next is True
        assert result.has_prev is True

    @pytest.mark.asyncio
    async def test_get_deck_public(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test getting a public deck without authentication."""
        sample_deck.is_public = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=None)

        assert result is not None
        assert result.id == sample_deck.id
        assert result.name == "Test Deck"

    @pytest.mark.asyncio
    async def test_get_deck_private_owner(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test getting a private deck as the owner."""
        sample_deck.is_public = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=sample_user)

        assert result is not None
        assert result.id == sample_deck.id

    @pytest.mark.asyncio
    async def test_get_deck_private_not_owner(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test getting a private deck as a different user returns None."""
        sample_deck.is_public = False

        other_user = MagicMock(spec=User)
        other_user.id = uuid4()  # Different user ID

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=other_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deck_private_no_auth(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test getting a private deck without auth returns None."""
        sample_deck.is_public = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deck_not_found(self, service: DeckService) -> None:
        """Test getting a non-existent deck returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(uuid4(), user=None)

        assert result is None


class TestDeckEndpoints:
    """Tests for deck API endpoints."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        return user

    @pytest.fixture
    def client(self, mock_db: AsyncMock, mock_user: MagicMock) -> TestClient:
        """Create test client with mocked dependencies."""
        from src.db.database import get_db
        from src.dependencies.auth import get_current_user, get_current_user_optional

        async def override_get_db():
            yield mock_db

        async def override_get_current_user():
            return mock_user

        async def override_get_current_user_optional():
            return mock_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_user_optional] = (
            override_get_current_user_optional
        )

        yield TestClient(app)

        app.dependency_overrides.clear()

    @pytest.fixture
    def unauthenticated_client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client without authentication."""
        from src.db.database import get_db
        from src.dependencies.auth import get_current_user_optional

        async def override_get_db():
            yield mock_db

        async def override_get_current_user_optional():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user_optional] = (
            override_get_current_user_optional
        )

        yield TestClient(app)

        app.dependency_overrides.clear()

    def test_create_deck_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test POST /api/v1/decks creates a deck."""
        from datetime import datetime

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Mock refresh to set server-side defaults
        async def mock_refresh(obj, attrs=None):
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        response = client.post(
            "/api/v1/decks",
            json={
                "name": "New Deck",
                "description": "My first deck",
                "format": "standard",
                "is_public": False,
                "cards": [],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Deck"
        assert data["description"] == "My first deck"
        assert data["format"] == "standard"
        assert data["is_public"] is False

    def test_create_deck_requires_name(self, client: TestClient) -> None:
        """Test POST /api/v1/decks requires name field."""
        response = client.post(
            "/api/v1/decks",
            json={"format": "standard"},
        )

        assert response.status_code == 422  # Validation error

    def test_create_deck_invalid_format(self, client: TestClient) -> None:
        """Test POST /api/v1/decks validates format enum."""
        response = client.post(
            "/api/v1/decks",
            json={"name": "Bad Deck", "format": "invalid_format"},
        )

        assert response.status_code == 422  # Validation error

    def test_list_decks_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test GET /api/v1/decks returns user's decks."""
        from datetime import datetime

        # Create mock deck
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = uuid4()
        mock_deck.user_id = mock_user.id
        mock_deck.name = "My Deck"
        mock_deck.format = "standard"
        mock_deck.archetype = None
        mock_deck.is_public = False
        mock_deck.cards = []
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_deck]
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # count
                mock_result,  # decks
            ]
        )

        response = client.get("/api/v1/decks")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "My Deck"

    def test_list_decks_pagination(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks respects pagination params."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=0)),
                mock_result,
            ]
        )

        response = client.get("/api/v1/decks?page=2&limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 50

    def test_get_deck_public(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/{id} returns public deck without auth."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()
        mock_deck.name = "Public Deck"
        mock_deck.description = None
        mock_deck.format = "standard"
        mock_deck.archetype = None
        mock_deck.is_public = True
        mock_deck.share_code = None
        mock_deck.cards = []
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)
        mock_deck.user = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = unauthenticated_client.get(f"/api/v1/decks/{deck_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Public Deck"

    def test_get_deck_private_forbidden(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/{id} returns 404 for private deck without auth."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()
        mock_deck.is_public = False
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = unauthenticated_client.get(f"/api/v1/decks/{deck_id}")

        # Returns 404 (not 403) to avoid leaking existence of private decks
        assert response.status_code == 404

    def test_get_deck_not_found(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test GET /api/v1/decks/{id} returns 404 for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get(f"/api/v1/decks/{uuid4()}")

        assert response.status_code == 404
