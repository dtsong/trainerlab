"""Tests for JP key_card_details enrichment (Issue #320).

Tests that JPNewArchetypeResponse includes key_card_details
with resolved card names and images alongside the raw key_cards.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.main import app
from src.models import JPNewArchetype


class TestJPKeyCardDetails:
    """Tests for key_card_details on JP archetype responses."""

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

    def _make_archetype(
        self,
        key_cards: list[str] | None = None,
    ) -> JPNewArchetype:
        """Create a JPNewArchetype model instance."""
        return JPNewArchetype(
            id=uuid4(),
            archetype_id="dragapult-ex",
            name="Dragapult ex",
            name_jp="ドラパルトex",
            key_cards=key_cards or ["sv6-89", "sv5-42"],
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.12"),
            jp_trend="rising",
            city_league_results=[],
            estimated_en_legal_date=date(2024, 6, 1),
            analysis="Strong archetype analysis.",
        )

    def test_key_card_details_populated(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test key_card_details has card_name/image_small."""
        archetype = self._make_archetype(key_cards=["sv6-89", "sv5-42"])

        # Mock: archetype query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [archetype]

        # Mock: count query
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # Mock: card info batch lookup
        card_row1 = MagicMock()
        card_row1.id = "sv6-89"
        card_row1.name = "Dragapult ex"
        card_row1.japanese_name = "ドラパルトex"
        card_row1.image_small = "https://img.example.com/sv6-89.png"

        card_row2 = MagicMock()
        card_row2.id = "sv5-42"
        card_row2.name = "Rare Candy"
        card_row2.japanese_name = None
        card_row2.image_small = "https://img.example.com/sv5-42.png"

        mock_card_result = MagicMock()
        mock_card_result.all.return_value = [
            card_row1,
            card_row2,
        ]

        mock_db.execute.side_effect = [
            mock_result,
            mock_count,
            mock_card_result,
        ]

        response = client.get("/api/v1/japan/archetypes/new")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1

        item = data["items"][0]

        # key_cards still present
        assert item["key_cards"] == ["sv6-89", "sv5-42"]

        # key_card_details populated
        assert item["key_card_details"] is not None
        assert len(item["key_card_details"]) == 2

        details = {d["card_id"]: d for d in item["key_card_details"]}
        assert details["sv6-89"]["card_name"] == "Dragapult ex"
        assert details["sv6-89"]["image_small"] == (
            "https://img.example.com/sv6-89.png"
        )
        assert details["sv5-42"]["card_name"] == "Rare Candy"
        assert details["sv5-42"]["image_small"] == (
            "https://img.example.com/sv5-42.png"
        )

    def test_key_card_details_null_for_unknown_ids(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test key_card_details has null fields for unknowns."""
        archetype = self._make_archetype(key_cards=["known-1", "unknown-1"])

        # Mock: archetype query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [archetype]

        # Mock: count query
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # Mock: card info lookup (only known-1 found)
        card_row = MagicMock()
        card_row.id = "known-1"
        card_row.name = "Iono"
        card_row.japanese_name = None
        card_row.image_small = "https://img.example.com/known-1.png"

        mock_card_result = MagicMock()
        mock_card_result.all.return_value = [card_row]

        mock_db.execute.side_effect = [
            mock_result,
            mock_count,
            mock_card_result,
        ]

        response = client.get("/api/v1/japan/archetypes/new")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        item = data["items"][0]
        details = {d["card_id"]: d for d in item["key_card_details"]}

        # Known card has name/image
        assert details["known-1"]["card_name"] == "Iono"
        assert details["known-1"]["image_small"] == (
            "https://img.example.com/known-1.png"
        )

        # Unknown card has null name/image
        assert details["unknown-1"]["card_name"] is None
        assert details["unknown-1"]["image_small"] is None

    def test_key_card_details_none_when_no_key_cards(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test key_card_details is None when no key_cards."""
        archetype = JPNewArchetype(
            id=uuid4(),
            archetype_id="empty-deck",
            name="Empty Deck",
            name_jp=None,
            key_cards=None,
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.05"),
            jp_trend="stable",
            city_league_results=None,
            estimated_en_legal_date=None,
            analysis=None,
        )

        # Mock: archetype query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [archetype]

        # Mock: count query
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # No card lookup needed (no key_cards)
        mock_db.execute.side_effect = [
            mock_result,
            mock_count,
        ]

        response = client.get("/api/v1/japan/archetypes/new")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        item = data["items"][0]
        assert item["key_cards"] is None
        assert item["key_card_details"] is None

    def test_key_card_details_graceful_on_card_lookup_error(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test card lookup failure still returns archetypes."""
        archetype = self._make_archetype(key_cards=["sv6-89"])

        # Mock: archetype query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [archetype]

        # Mock: count query
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # Mock: card lookup fails
        mock_db.execute.side_effect = [
            mock_result,
            mock_count,
            SQLAlchemyError("Card lookup failed"),
        ]

        response = client.get("/api/v1/japan/archetypes/new")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        item = data["items"][0]
        # key_cards still present
        assert item["key_cards"] == ["sv6-89"]
        # key_card_details present but with null info
        assert item["key_card_details"] is not None
        assert len(item["key_card_details"]) == 1
        assert item["key_card_details"][0]["card_name"] is None
        assert item["key_card_details"][0]["image_small"] is None

    def test_multiple_archetypes_share_card_lookup(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test multiple archetypes batch-share card lookup."""
        arch1 = self._make_archetype(key_cards=["sv6-89"])
        arch1.archetype_id = "deck-a"
        arch1.name = "Deck A"

        arch2 = JPNewArchetype(
            id=uuid4(),
            archetype_id="deck-b",
            name="Deck B",
            name_jp=None,
            key_cards=["sv6-89", "sv5-10"],
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.08"),
            jp_trend="falling",
            city_league_results=None,
            estimated_en_legal_date=None,
            analysis=None,
        )

        # Mock: archetype query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            arch1,
            arch2,
        ]

        # Mock: count query
        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        # Mock: card lookup (both card IDs in single batch)
        card_row1 = MagicMock()
        card_row1.id = "sv6-89"
        card_row1.name = "Dragapult ex"
        card_row1.japanese_name = None
        card_row1.image_small = "https://img.example.com/sv6-89.png"
        card_row2 = MagicMock()
        card_row2.id = "sv5-10"
        card_row2.name = "Boss's Orders"
        card_row2.japanese_name = None
        card_row2.image_small = "https://img.example.com/sv5-10.png"
        mock_card_result = MagicMock()
        mock_card_result.all.return_value = [
            card_row1,
            card_row2,
        ]

        mock_db.execute.side_effect = [
            mock_result,
            mock_count,
            mock_card_result,
        ]

        response = client.get("/api/v1/japan/archetypes/new")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2

        # Deck A uses sv6-89
        item_a = data["items"][0]
        assert len(item_a["key_card_details"]) == 1
        assert item_a["key_card_details"][0]["card_name"] == "Dragapult ex"

        # Deck B uses sv6-89 and sv5-10
        item_b = data["items"][1]
        assert len(item_b["key_card_details"]) == 2
        details_b = {d["card_id"]: d for d in item_b["key_card_details"]}
        assert details_b["sv6-89"]["card_name"] == "Dragapult ex"
        assert details_b["sv5-10"]["card_name"] == "Boss's Orders"


class TestJPKeyCardInfoSchema:
    """Tests for JPKeyCardInfo Pydantic schema."""

    def test_jp_key_card_info_with_all_fields(self) -> None:
        """Test JPKeyCardInfo with all fields populated."""
        from src.schemas.japan import JPKeyCardInfo

        info = JPKeyCardInfo(
            card_id="sv6-89",
            card_name="Dragapult ex",
            image_small="https://img.example.com/sv6-89.png",
        )
        assert info.card_id == "sv6-89"
        assert info.card_name == "Dragapult ex"
        assert info.image_small == ("https://img.example.com/sv6-89.png")

    def test_jp_key_card_info_defaults_to_none(self) -> None:
        """Test JPKeyCardInfo defaults card_name/image."""
        from src.schemas.japan import JPKeyCardInfo

        info = JPKeyCardInfo(card_id="sv6-89")
        assert info.card_id == "sv6-89"
        assert info.card_name is None
        assert info.image_small is None

    def test_jp_new_archetype_response_has_field(
        self,
    ) -> None:
        """Test JPNewArchetypeResponse has key_card_details."""
        from src.schemas.japan import (
            JPKeyCardInfo,
            JPNewArchetypeResponse,
        )

        resp = JPNewArchetypeResponse(
            id="test-id",
            archetype_id="test-arch",
            name="Test",
            key_cards=["card-1"],
            key_card_details=[
                JPKeyCardInfo(
                    card_id="card-1",
                    card_name="Test Card",
                    image_small="https://img.example.com/1.png",
                ),
            ],
            jp_meta_share=0.1,
        )
        assert resp.key_card_details is not None
        assert len(resp.key_card_details) == 1
        assert resp.key_card_details[0].card_name == "Test Card"

    def test_jp_new_archetype_response_details_optional(
        self,
    ) -> None:
        """Test key_card_details defaults to None."""
        from src.schemas.japan import JPNewArchetypeResponse

        resp = JPNewArchetypeResponse(
            id="test-id",
            archetype_id="test-arch",
            name="Test",
            jp_meta_share=0.1,
        )
        assert resp.key_card_details is None


class TestArchetypeToResponseHelper:
    """Unit tests for _archetype_to_response helper."""

    def test_archetype_to_response_with_card_info(
        self,
    ) -> None:
        """Test _archetype_to_response enriches details."""
        from src.routers.japan import _archetype_to_response

        archetype = JPNewArchetype(
            id=uuid4(),
            archetype_id="test-deck",
            name="Test Deck",
            name_jp=None,
            key_cards=["card-a", "card-b"],
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.10"),
            jp_trend="stable",
            city_league_results=None,
            estimated_en_legal_date=None,
            analysis=None,
        )

        card_info = {
            "card-a": (
                "Card Alpha",
                "https://img.example.com/a.png",
            ),
            "card-b": (
                "Card Beta",
                "https://img.example.com/b.png",
            ),
        }

        result = _archetype_to_response(archetype, card_info=card_info)

        assert result.key_card_details is not None
        assert len(result.key_card_details) == 2
        details = {d.card_id: d for d in result.key_card_details}
        assert details["card-a"].card_name == "Card Alpha"
        assert details["card-a"].image_small == ("https://img.example.com/a.png")
        assert details["card-b"].card_name == "Card Beta"

    def test_archetype_to_response_without_card_info(
        self,
    ) -> None:
        """Test _archetype_to_response with no card_info."""
        from src.routers.japan import _archetype_to_response

        archetype = JPNewArchetype(
            id=uuid4(),
            archetype_id="test-deck",
            name="Test Deck",
            name_jp=None,
            key_cards=["card-a"],
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.10"),
            jp_trend="stable",
            city_league_results=None,
            estimated_en_legal_date=None,
            analysis=None,
        )

        result = _archetype_to_response(archetype)

        assert result.key_card_details is not None
        assert len(result.key_card_details) == 1
        assert result.key_card_details[0].card_name is None
        assert result.key_card_details[0].image_small is None

    def test_archetype_to_response_no_key_cards(
        self,
    ) -> None:
        """Test _archetype_to_response with None key_cards."""
        from src.routers.japan import _archetype_to_response

        archetype = JPNewArchetype(
            id=uuid4(),
            archetype_id="empty-deck",
            name="Empty Deck",
            name_jp=None,
            key_cards=None,
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.05"),
            jp_trend="stable",
            city_league_results=None,
            estimated_en_legal_date=None,
            analysis=None,
        )

        result = _archetype_to_response(archetype)

        assert result.key_card_details is None
