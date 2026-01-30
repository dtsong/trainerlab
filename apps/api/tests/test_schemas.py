"""Tests for Pydantic schemas."""

from datetime import date, datetime

from src.schemas.card import (
    AttackSchema,
    CardResponse,
    CardSummaryResponse,
    SetSummaryResponse,
)
from src.schemas.pagination import PaginatedResponse


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
