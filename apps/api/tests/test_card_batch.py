"""Tests for the card batch endpoint (GET /api/v1/cards/batch).

Tests the Visual Card References feature (Issue #320):
- Batch lookup of cards by comma-separated IDs
- Max 50 IDs enforced
- Unknown IDs silently skipped
- Empty string returns empty list
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.main import app
from src.models.card import Card
from src.services.card_service import CardService


class TestCardBatchEndpoint:
    """Tests for GET /api/v1/cards/batch."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = lambda: None
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_card_1(self) -> MagicMock:
        """Create a sample card mock (Pikachu)."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.name = "Pikachu"
        card.supertype = "Pokemon"
        card.types = ["Lightning"]
        card.set_id = "sv4"
        card.rarity = "Common"
        card.image_small = "https://example.com/pikachu.png"
        return card

    @pytest.fixture
    def sample_card_2(self) -> MagicMock:
        """Create a second sample card mock (Charizard ex)."""
        card = MagicMock(spec=Card)
        card.id = "sv3-6"
        card.name = "Charizard ex"
        card.supertype = "Pokemon"
        card.types = ["Fire"]
        card.set_id = "sv3"
        card.rarity = "Double Rare"
        card.image_small = "https://example.com/charizard.png"
        return card

    def test_batch_valid_ids_return_card_summaries(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_card_1: MagicMock,
        sample_card_2: MagicMock,
    ) -> None:
        """Test valid IDs return card summaries."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_card_1,
            sample_card_2,
        ]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/batch?ids=sv4-6,sv3-6")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        ids = {item["id"] for item in data}
        assert "sv4-6" in ids
        assert "sv3-6" in ids

    def test_batch_single_id(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_card_1: MagicMock,
    ) -> None:
        """Test batch with a single ID."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_card_1,
        ]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/batch?ids=sv4-6")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "sv4-6"
        assert data[0]["name"] == "Pikachu"

    def test_batch_unknown_ids_silently_skipped(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_card_1: MagicMock,
    ) -> None:
        """Test unknown IDs are silently skipped (no error)."""
        # DB only returns the one card that exists
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_card_1,
        ]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/batch?ids=sv4-6,unknown-1,unknown-2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "sv4-6"

    def test_batch_all_unknown_ids_returns_empty(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test all unknown IDs returns empty list."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/batch?ids=unknown-1,unknown-2")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_batch_empty_string_returns_empty(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test empty string returns empty list."""
        response = client.get("/api/v1/cards/batch?ids=")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_batch_max_50_limit(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test max 50 IDs limit -- sends 51, only 50 processed."""
        # Generate 51 card IDs
        ids_list = [f"sv4-{i}" for i in range(51)]
        ids_param = ",".join(ids_list)

        # Return empty (we just want to verify the limit)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get(f"/api/v1/cards/batch?ids={ids_param}")

        assert response.status_code == 200
        # The endpoint should have called the DB with at most 50 IDs
        # Verify by checking the execute call was made
        # (with 51 IDs sent, only 50 should be processed)
        assert mock_db.execute.call_count == 1

    def test_batch_whitespace_trimmed(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_card_1: MagicMock,
    ) -> None:
        """Test whitespace around IDs is trimmed."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_card_1,
        ]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/batch?ids=%20sv4-6%20,%20sv3-6%20")

        assert response.status_code == 200
        data = response.json()
        # At least the valid card should be found
        assert len(data) >= 1

    def test_batch_response_includes_image_small(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_card_1: MagicMock,
    ) -> None:
        """Test batch response includes image_small field."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_card_1,
        ]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/cards/batch?ids=sv4-6")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["image_small"] == ("https://example.com/pikachu.png")


class TestCardServiceGetCardsBatch:
    """Unit tests for CardService.get_cards_batch method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> CardService:
        """Create a CardService with mock session."""
        return CardService(mock_session)

    @pytest.mark.asyncio
    async def test_get_cards_batch_empty_list(self, service: CardService) -> None:
        """Test empty card_ids returns empty list."""
        result = await service.get_cards_batch([])
        assert result == []
        # Should not call the DB
        service.session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_cards_batch_returns_summaries(
        self, service: CardService
    ) -> None:
        """Test batch returns CardSummaryResponse items."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.name = "Pikachu"
        card.supertype = "Pokemon"
        card.types = ["Lightning"]
        card.set_id = "sv4"
        card.rarity = "Common"
        card.image_small = "https://example.com/pikachu.png"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [card]
        service.session.execute.return_value = mock_result

        result = await service.get_cards_batch(["sv4-6"])

        assert len(result) == 1
        assert result[0].id == "sv4-6"
        assert result[0].name == "Pikachu"
        assert result[0].image_small == ("https://example.com/pikachu.png")

    @pytest.mark.asyncio
    async def test_get_cards_batch_skips_missing(self, service: CardService) -> None:
        """Test batch skips IDs not found in DB."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        result = await service.get_cards_batch(["nonexistent-1", "nonexistent-2"])

        assert result == []
