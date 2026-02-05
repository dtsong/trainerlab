"""Schemas for placeholder card management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AttackSchema(BaseModel):
    """Schema for card attacks."""

    name: str
    cost: list[str]
    damage: str | None = None
    text: str | None = None


class PlaceholderCardCreate(BaseModel):
    """Schema for creating a placeholder card."""

    jp_card_id: str = Field(
        ..., description="Original Japanese card ID (e.g., SV10-15)"
    )
    name_jp: str = Field(..., description="Japanese card name")
    name_en: str = Field(..., description="English translated name")
    supertype: str = Field(..., description="Card supertype (Pokemon, Trainer, Energy)")
    subtypes: list[str] | None = Field(
        None, description="Card subtypes (Basic, Stage 1, V, etc.)"
    )
    hp: int | None = Field(None, description="HP for Pokemon cards")
    types: list[str] | None = Field(None, description="Card types (Fire, Water, etc.)")
    attacks: list[AttackSchema] | None = Field(
        None, description="Attacks for Pokemon cards"
    )
    source: str = Field("manual", description="Source of translation")
    source_url: str | None = Field(None, description="Link to original post")
    source_account: str | None = Field(None, description="Social media account")


class PlaceholderCardUpdate(BaseModel):
    """Schema for updating a placeholder card."""

    name_en: str | None = None
    supertype: str | None = None
    subtypes: list[str] | None = None
    hp: int | None = None
    types: list[str] | None = None
    attacks: list[AttackSchema] | None = None
    source_url: str | None = None
    is_unreleased: bool | None = None


class PlaceholderCardResponse(BaseModel):
    """Schema for placeholder card response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    jp_card_id: str
    en_card_id: str
    name_jp: str
    name_en: str
    supertype: str
    subtypes: list[str] | None
    hp: int | None
    types: list[str] | None
    attacks: list[dict[str, Any]] | None
    set_code: str
    official_set_code: str | None
    is_unreleased: bool
    is_released: bool
    released_at: datetime | None
    source: str
    source_url: str | None
    source_account: str | None
    created_at: datetime
    updated_at: datetime


class PlaceholderListResponse(BaseModel):
    """Schema for paginated placeholder card list."""

    total: int
    items: list[PlaceholderCardResponse]
    limit: int
    offset: int


class TranslationFetchRequest(BaseModel):
    """Schema for fetching translations from social media."""

    accounts: list[str] = Field(
        ..., description="List of X/BlueSky accounts to monitor"
    )
    since_date: str = Field(..., description="Fetch posts since this date (YYYY-MM-DD)")
    dry_run: bool = Field(False, description="If true, don't save to database")


class TranslationFetchResponse(BaseModel):
    """Schema for translation fetch response."""

    accounts_checked: list[str]
    posts_fetched: int
    translations_parsed: int
    placeholders_created: int
    dry_run: bool
    message: str | None = None
