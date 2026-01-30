"""Tests for Pydantic schemas."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.card import (
    AttackSchema,
    CardResponse,
    CardSummaryResponse,
    SetSummaryResponse,
)
from src.schemas.deck import (
    CardInDeck,
    DeckCreate,
    DeckResponse,
    DeckSummaryResponse,
    DeckUpdate,
    UserSummary,
)
from src.schemas.pagination import PaginatedResponse
from src.schemas.set import SetResponse


class TestCardSchemas:
    """Tests for card-related schemas."""

    def test_attack_schema(self):
        """Test AttackSchema validation."""
        attack = AttackSchema(
            name="Find a Friend",
            cost=["Grass"],
            damage="50+",
            effect="Search your deck for up to 2 Pokemon.",
        )
        assert attack.name == "Find a Friend"
        assert attack.cost == ["Grass"]
        assert attack.damage == "50+"

    def test_attack_schema_minimal(self):
        """Test AttackSchema with minimal fields."""
        attack = AttackSchema(name="Quick Attack", cost=["Colorless"])
        assert attack.name == "Quick Attack"
        assert attack.damage is None
        assert attack.effect is None

    def test_set_summary_response(self):
        """Test SetSummaryResponse schema."""
        set_data = SetSummaryResponse(
            id="swsh1",
            name="Sword & Shield",
            series="Sword & Shield",
            release_date=date(2020, 2, 7),
            logo_url="https://example.com/logo.png",
        )
        assert set_data.id == "swsh1"
        assert set_data.release_date == date(2020, 2, 7)

    def test_card_summary_response(self):
        """Test CardSummaryResponse schema."""
        card = CardSummaryResponse(
            id="swsh1-1",
            name="Celebi V",
            supertype="Pokemon",
            types=["Grass"],
            set_id="swsh1",
            image_small="https://example.com/card.png",
        )
        assert card.id == "swsh1-1"
        assert card.types == ["Grass"]

    def test_card_response_full(self):
        """Test CardResponse with all fields."""
        card = CardResponse(
            id="swsh1-1",
            local_id="1",
            name="Celebi V",
            japanese_name="セレビィV",
            supertype="Pokemon",
            subtypes=["V"],
            types=["Grass"],
            hp=180,
            stage="Basic",
            evolves_from=None,
            evolves_to=None,
            attacks=[
                {
                    "name": "Find a Friend",
                    "cost": ["Grass"],
                    "effect": "Search your deck.",
                }
            ],
            abilities=None,
            weaknesses=[{"type": "Fire", "value": "×2"}],
            resistances=None,
            retreat_cost=1,
            rules=None,
            set_id="swsh1",
            rarity="Holo Rare V",
            number="1",
            image_small="https://example.com/small.png",
            image_large="https://example.com/large.png",
            regulation_mark="D",
            legalities={"standard": False, "expanded": True},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert card.id == "swsh1-1"
        assert card.japanese_name == "セレビィV"
        assert card.hp == 180
        assert len(card.attacks) == 1
        assert card.legalities["expanded"] is True

    def test_card_response_minimal(self):
        """Test CardResponse with minimal required fields."""
        card = CardResponse(
            id="swsh1-1",
            local_id="1",
            name="Celebi V",
            supertype="Pokemon",
            set_id="swsh1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert card.id == "swsh1-1"
        assert card.hp is None
        assert card.attacks is None


class TestPaginationSchemas:
    """Tests for pagination schemas."""

    def test_paginated_response_cards(self):
        """Test PaginatedResponse with card items."""
        cards = [
            CardSummaryResponse(
                id=f"swsh1-{i}",
                name=f"Card {i}",
                supertype="Pokemon",
                set_id="swsh1",
            )
            for i in range(10)
        ]
        response = PaginatedResponse[CardSummaryResponse](
            items=cards,
            total=100,
            page=1,
            limit=10,
            has_next=True,
            has_prev=False,
        )
        assert len(response.items) == 10
        assert response.total == 100
        assert response.page == 1
        assert response.has_next is True
        assert response.has_prev is False

    def test_paginated_response_with_cursor(self):
        """Test PaginatedResponse with cursor pagination."""
        response = PaginatedResponse[CardSummaryResponse](
            items=[],
            total=0,
            page=1,
            limit=10,
            has_next=False,
            has_prev=False,
            next_cursor="abc123",
        )
        assert response.next_cursor == "abc123"

    def test_paginated_response_empty(self):
        """Test PaginatedResponse with no items."""
        response = PaginatedResponse[CardSummaryResponse](
            items=[],
            total=0,
            page=1,
            limit=10,
            has_next=False,
            has_prev=False,
        )
        assert len(response.items) == 0
        assert response.total == 0

    def test_paginated_response_pages_property(self):
        """Test PaginatedResponse total_pages calculation."""
        response = PaginatedResponse[CardSummaryResponse](
            items=[],
            total=95,
            page=1,
            limit=10,
            has_next=True,
            has_prev=False,
        )
        assert response.total_pages == 10  # ceil(95/10) = 10

    def test_paginated_response_serialization(self):
        """Test PaginatedResponse serializes correctly."""
        response = PaginatedResponse[CardSummaryResponse](
            items=[
                CardSummaryResponse(
                    id="swsh1-1",
                    name="Celebi V",
                    supertype="Pokemon",
                    set_id="swsh1",
                )
            ],
            total=1,
            page=1,
            limit=10,
            has_next=False,
            has_prev=False,
        )
        data = response.model_dump()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        assert data["total_pages"] == 1


class TestSetSchemas:
    """Tests for set-related schemas."""

    def test_set_response_full(self):
        """Test SetResponse with all fields."""
        set_data = SetResponse(
            id="sv4",
            name="Paradox Rift",
            series="Scarlet & Violet",
            release_date=date(2023, 11, 3),
            release_date_jp=date(2023, 9, 22),
            card_count=266,
            logo_url="https://example.com/logo.png",
            symbol_url="https://example.com/symbol.png",
            legalities={"standard": "Legal", "expanded": "Legal"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert set_data.id == "sv4"
        assert set_data.name == "Paradox Rift"
        assert set_data.card_count == 266
        assert set_data.legalities["standard"] == "Legal"

    def test_set_response_minimal(self):
        """Test SetResponse with minimal required fields."""
        set_data = SetResponse(
            id="sv4",
            name="Paradox Rift",
            series="Scarlet & Violet",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert set_data.id == "sv4"
        assert set_data.release_date is None
        assert set_data.card_count is None


class TestDeckSchemas:
    """Tests for deck-related schemas."""

    def test_card_in_deck(self):
        """Test CardInDeck validation."""
        card = CardInDeck(card_id="sv4-6", quantity=4)
        assert card.card_id == "sv4-6"
        assert card.quantity == 4

    def test_card_in_deck_quantity_bounds(self):
        """Test CardInDeck quantity validation bounds."""
        # Valid: 1 copy
        card = CardInDeck(card_id="sv4-6", quantity=1)
        assert card.quantity == 1

        # Valid: 60 copies (max for basic energy)
        card = CardInDeck(card_id="sv4-257", quantity=60)
        assert card.quantity == 60

        # Invalid: 0 copies
        with pytest.raises(ValidationError):
            CardInDeck(card_id="sv4-6", quantity=0)

        # Invalid: 61 copies
        with pytest.raises(ValidationError):
            CardInDeck(card_id="sv4-6", quantity=61)

    def test_user_summary(self):
        """Test UserSummary schema."""
        user_id = uuid4()
        user = UserSummary(id=user_id, username="trainer123")
        assert user.id == user_id
        assert user.username == "trainer123"

    def test_deck_create_full(self):
        """Test DeckCreate with all fields."""
        deck = DeckCreate(
            name="My Charizard Deck",
            description="A competitive Charizard ex deck",
            cards=[
                CardInDeck(card_id="sv4-6", quantity=4),
                CardInDeck(card_id="sv4-125", quantity=2),
            ],
            format="standard",
            is_public=True,
        )
        assert deck.name == "My Charizard Deck"
        assert deck.description == "A competitive Charizard ex deck"
        assert len(deck.cards) == 2
        assert deck.format == "standard"
        assert deck.is_public is True

    def test_deck_create_minimal(self):
        """Test DeckCreate with only required fields."""
        deck = DeckCreate(name="Untitled Deck")
        assert deck.name == "Untitled Deck"
        assert deck.description is None
        assert deck.cards == []
        assert deck.format == "standard"
        assert deck.is_public is False

    def test_deck_create_name_validation(self):
        """Test DeckCreate name validation."""
        # Valid name
        deck = DeckCreate(name="A" * 255)
        assert len(deck.name) == 255

        # Empty name is invalid
        with pytest.raises(ValidationError):
            DeckCreate(name="")

        # Name too long
        with pytest.raises(ValidationError):
            DeckCreate(name="A" * 256)

    def test_deck_create_format_validation(self):
        """Test DeckCreate format validation."""
        # Valid formats
        deck_standard = DeckCreate(name="Test", format="standard")
        assert deck_standard.format == "standard"

        deck_expanded = DeckCreate(name="Test", format="expanded")
        assert deck_expanded.format == "expanded"

        # Invalid format
        with pytest.raises(ValidationError):
            DeckCreate(name="Test", format="unlimited")

    def test_deck_update_partial(self):
        """Test DeckUpdate with partial fields."""
        # Update only name
        update = DeckUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.description is None
        assert update.cards is None
        assert update.format is None
        assert update.is_public is None

    def test_deck_update_all_fields(self):
        """Test DeckUpdate with all fields."""
        update = DeckUpdate(
            name="Updated Deck",
            description="Updated description",
            cards=[CardInDeck(card_id="sv4-6", quantity=3)],
            format="expanded",
            archetype="Charizard ex",
            is_public=True,
        )
        assert update.name == "Updated Deck"
        assert update.format == "expanded"
        assert update.archetype == "Charizard ex"

    def test_deck_update_empty(self):
        """Test DeckUpdate with no fields (valid for no-op)."""
        update = DeckUpdate()
        assert update.name is None
        assert update.cards is None

    def test_deck_response_full(self):
        """Test DeckResponse with all fields."""
        deck_id = uuid4()
        user_id = uuid4()
        now = datetime.now()

        deck = DeckResponse(
            id=deck_id,
            user_id=user_id,
            name="Championship Deck",
            description="My best deck",
            cards=[
                CardInDeck(card_id="sv4-6", quantity=4),
                CardInDeck(card_id="sv4-125", quantity=2),
            ],
            format="standard",
            archetype="Charizard ex",
            is_public=True,
            share_code="ABC123",
            created_at=now,
            updated_at=now,
            user=UserSummary(id=user_id, username="champion"),
        )
        assert deck.id == deck_id
        assert deck.name == "Championship Deck"
        assert len(deck.cards) == 2
        assert deck.user.username == "champion"

    def test_deck_response_minimal(self):
        """Test DeckResponse with minimal required fields."""
        deck_id = uuid4()
        user_id = uuid4()
        now = datetime.now()

        deck = DeckResponse(
            id=deck_id,
            user_id=user_id,
            name="Test Deck",
            format="standard",
            is_public=False,
            created_at=now,
            updated_at=now,
        )
        assert deck.id == deck_id
        assert deck.description is None
        assert deck.cards == []
        assert deck.archetype is None
        assert deck.share_code is None
        assert deck.user is None

    def test_deck_summary_response(self):
        """Test DeckSummaryResponse for list views."""
        deck_id = uuid4()
        user_id = uuid4()
        now = datetime.now()

        summary = DeckSummaryResponse(
            id=deck_id,
            user_id=user_id,
            name="Quick Deck",
            format="standard",
            archetype="Gardevoir ex",
            is_public=True,
            card_count=60,
            created_at=now,
            updated_at=now,
        )
        assert summary.id == deck_id
        assert summary.name == "Quick Deck"
        assert summary.card_count == 60

    def test_deck_response_serialization(self):
        """Test DeckResponse serializes correctly."""
        deck_id = uuid4()
        user_id = uuid4()
        now = datetime.now()

        deck = DeckResponse(
            id=deck_id,
            user_id=user_id,
            name="Test",
            format="standard",
            is_public=False,
            created_at=now,
            updated_at=now,
        )
        data = deck.model_dump()

        assert "id" in data
        assert "user_id" in data
        assert "name" in data
        assert "cards" in data
        assert "format" in data
        assert "created_at" in data
