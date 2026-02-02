"""User schemas for API request/response models."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """User response model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    preferences: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class UserPreferencesUpdate(BaseModel):
    """Update user preferences.

    All fields are optional - only provided fields will be updated.
    """

    theme: Literal["light", "dark", "system"] | None = Field(
        None, description="UI theme (light, dark, system)"
    )
    default_format: Literal["standard", "expanded"] | None = Field(
        None, description="Default deck format (standard, expanded)"
    )
    email_notifications: bool | None = Field(
        None, description="Enable email notifications"
    )
