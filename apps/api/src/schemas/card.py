"""Card-related Pydantic schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AttackSchema(BaseModel):
    """Schema for card attack data."""

    model_config = ConfigDict(extra="allow")

    name: str
    cost: list[str]
    damage: str | None = None
    effect: str | None = None


class AbilitySchema(BaseModel):
    """Schema for card ability data."""

    model_config = ConfigDict(extra="allow")

    name: str
    type: str | None = None
    effect: str | None = None


class WeaknessResistanceSchema(BaseModel):
    """Schema for weakness/resistance data."""

    model_config = ConfigDict(extra="allow")

    type: str
    value: str


class SetSummaryResponse(BaseModel):
    """Summary schema for card set data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    series: str
    release_date: date | None = None
    logo_url: str | None = None
    symbol_url: str | None = None


class CardSummaryResponse(BaseModel):
    """Summary schema for card data (used in lists)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    supertype: str
    types: list[str] | None = None
    set_id: str
    rarity: str | None = None
    image_small: str | None = None


class CardResponse(BaseModel):
    """Full schema for card data."""

    model_config = ConfigDict(from_attributes=True)

    # Identifiers
    id: str
    local_id: str
    name: str
    japanese_name: str | None = None

    # Card type
    supertype: str
    subtypes: list[str] | None = None
    types: list[str] | None = None

    # Pokemon stats
    hp: int | None = None
    stage: str | None = None
    evolves_from: str | None = None
    evolves_to: list[str] | None = None

    # Game mechanics
    attacks: list[dict[str, Any]] | None = None
    abilities: list[dict[str, Any]] | None = None
    weaknesses: list[dict[str, Any]] | None = None
    resistances: list[dict[str, Any]] | None = None
    retreat_cost: int | None = None
    rules: list[str] | None = None

    # Set info
    set_id: str
    rarity: str | None = None
    number: str | None = None

    # Images
    image_small: str | None = None
    image_large: str | None = None

    # Legality
    regulation_mark: str | None = None
    legalities: dict[str, bool] | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Nested relationships (optional, for expanded responses)
    set: SetSummaryResponse | None = None
