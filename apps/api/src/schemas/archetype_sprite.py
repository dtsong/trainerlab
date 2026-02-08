"""Schemas for archetype sprite management."""

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SPRITE_KEY_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


class ArchetypeSpriteCreate(BaseModel):
    """Schema for creating an archetype sprite mapping."""

    sprite_key: str = Field(min_length=1, max_length=255)
    archetype_name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Custom display name (overrides archetype_name in UI)",
    )

    @field_validator("sprite_key")
    @classmethod
    def validate_sprite_key(cls, v: str) -> str:
        v = v.strip().lower()
        if not _SPRITE_KEY_RE.match(v):
            msg = (
                "sprite_key must be lowercase alphanumeric "
                "with hyphens (e.g. 'charizard-pidgeot')"
            )
            raise ValueError(msg)
        return v


class ArchetypeSpriteUpdate(BaseModel):
    """Schema for updating an archetype sprite mapping."""

    archetype_name: str | None = Field(default=None, min_length=1, max_length=255)
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="Custom display name (overrides archetype_name in UI)",
    )


class ArchetypeSpriteResponse(BaseModel):
    """Schema for archetype sprite response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sprite_key: str
    archetype_name: str
    display_name: str | None = None


class ArchetypeSpriteListResponse(BaseModel):
    """Schema for archetype sprite list response."""

    total: int
    items: list[ArchetypeSpriteResponse]
