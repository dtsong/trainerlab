"""API key-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Display name for the key"
    )
    monthly_limit: int = Field(
        1000, ge=100, le=100000, description="Monthly request limit"
    )


class ApiKeyResponse(BaseModel):
    """Schema for API key data in responses (no full key)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    key_prefix: str
    name: str
    monthly_limit: int
    requests_this_month: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ApiKeyCreatedResponse(BaseModel):
    """Schema for newly created API key (includes full key)."""

    api_key: ApiKeyResponse
    full_key: str = Field(
        ...,
        description="Full API key (only shown once on creation)",
    )


class ApiKeyListResponse(BaseModel):
    """Schema for API key list."""

    items: list[ApiKeyResponse]
    total: int
