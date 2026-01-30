"""Deck-related Pydantic schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CardInDeck(BaseModel):
    """Schema for a card entry in a deck."""

    card_id: str = Field(..., description="The card ID (e.g., 'sv4-6')")
    quantity: int = Field(..., ge=1, le=60, description="Number of copies (1-60)")


class UserSummary(BaseModel):
    """Summary schema for user data in deck responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str


# Issue #98: DeckCreate Pydantic model
class DeckCreate(BaseModel):
    """Schema for creating a new deck."""

    name: str = Field(..., min_length=1, max_length=255, description="Deck name")
    description: str | None = Field(
        None, max_length=5000, description="Deck description"
    )
    cards: list[CardInDeck] = Field(
        default_factory=list, description="Cards in the deck"
    )
    format: Literal["standard", "expanded"] = Field(
        "standard", description="Deck format"
    )
    is_public: bool = Field(False, description="Whether the deck is publicly visible")


# Issue #99: DeckUpdate Pydantic model
class DeckUpdate(BaseModel):
    """Schema for updating an existing deck. All fields are optional."""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Deck name"
    )
    description: str | None = Field(
        None, max_length=5000, description="Deck description"
    )
    cards: list[CardInDeck] | None = Field(None, description="Cards in the deck")
    format: Literal["standard", "expanded"] | None = Field(
        None, description="Deck format"
    )
    archetype: str | None = Field(None, max_length=255, description="Deck archetype")
    is_public: bool | None = Field(
        None, description="Whether the deck is publicly visible"
    )


# Issue #100: DeckResponse Pydantic model
class DeckResponse(BaseModel):
    """Full schema for deck data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    # Identifiers
    id: UUID
    user_id: UUID

    # Deck info
    name: str
    description: str | None = None

    # Cards
    cards: list[CardInDeck] = Field(default_factory=list)

    # Format and archetype
    format: Literal["standard", "expanded"]
    archetype: str | None = None

    # Sharing
    is_public: bool
    share_code: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Nested relationships (optional, for expanded responses)
    user: UserSummary | None = None


class DeckSummaryResponse(BaseModel):
    """Summary schema for deck data (used in lists)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    format: Literal["standard", "expanded"]
    archetype: str | None = None
    is_public: bool
    card_count: int = Field(0, description="Total number of cards in deck")
    created_at: datetime
    updated_at: datetime
