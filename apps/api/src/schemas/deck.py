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


class TypeBreakdown(BaseModel):
    """Count of cards by supertype."""

    pokemon: int = Field(0, description="Number of Pokemon cards")
    trainer: int = Field(0, description="Number of Trainer cards")
    energy: int = Field(0, description="Number of Energy cards")


class EnergyCurvePoint(BaseModel):
    """Energy cost distribution for attacks."""

    cost: int = Field(..., description="Energy cost (0, 1, 2, etc.)")
    count: int = Field(..., description="Number of attacks at this cost")


class DeckStatsResponse(BaseModel):
    """Statistics about a deck's composition."""

    type_breakdown: TypeBreakdown = Field(
        ..., description="Count of cards by supertype"
    )
    average_hp: float | None = Field(
        None, description="Average HP of Pokemon cards (null if no Pokemon)"
    )
    energy_curve: list[EnergyCurvePoint] = Field(
        default_factory=list,
        description="Distribution of attack costs",
    )
    total_cards: int = Field(..., description="Total number of cards in deck")


class DeckImportRequest(BaseModel):
    """Request body for importing a deck from text."""

    deck_list: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Deck list text in PTCGO or Pokemon Card Live format",
    )


class UnmatchedCard(BaseModel):
    """Info about a card that could not be matched in the database."""

    line: str = Field(..., description="Original line from the deck list")
    name: str = Field(..., description="Parsed card name")
    set_code: str = Field(..., description="Parsed set code")
    number: str = Field(..., description="Parsed card number")
    quantity: int = Field(..., ge=1, description="Parsed quantity")


class DeckImportResponse(BaseModel):
    """Response from importing a deck."""

    cards: list[CardInDeck] = Field(
        default_factory=list, description="Successfully matched cards"
    )
    unmatched: list[UnmatchedCard] = Field(
        default_factory=list, description="Cards that could not be matched"
    )
    total_cards: int = Field(..., ge=0, description="Total number of cards matched")
