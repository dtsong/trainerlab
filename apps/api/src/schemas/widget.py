"""Widget-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

WIDGET_TYPES = Literal[
    "meta_snapshot",
    "archetype_card",
    "meta_pie",
    "meta_trend",
    "jp_comparison",
    "deck_cost",
    "tournament_result",
    "prediction",
    "evolution_timeline",
]


class WidgetCreate(BaseModel):
    """Schema for creating a new widget."""

    type: WIDGET_TYPES = Field(..., description="Widget type")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Widget configuration"
    )
    theme: Literal["light", "dark"] = Field("dark", description="Widget theme")
    accent_color: str | None = Field(
        None, max_length=20, description="Accent color hex code"
    )
    show_attribution: bool = Field(True, description="Show TrainerLab attribution")


class WidgetUpdate(BaseModel):
    """Schema for updating a widget."""

    config: dict[str, Any] | None = Field(None, description="Widget configuration")
    theme: Literal["light", "dark"] | None = Field(None, description="Widget theme")
    accent_color: str | None = Field(None, max_length=20, description="Accent color")
    show_attribution: bool | None = Field(None, description="Show attribution")
    is_active: bool | None = Field(None, description="Widget active status")


class WidgetResponse(BaseModel):
    """Schema for widget data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: str
    config: dict[str, Any]
    theme: str
    accent_color: str | None = None
    show_attribution: bool
    embed_count: int
    view_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WidgetDataResponse(BaseModel):
    """Schema for resolved widget data."""

    widget_id: str
    type: str
    theme: str
    accent_color: str | None = None
    show_attribution: bool
    data: dict[str, Any]
    error: str | None = None


class WidgetEmbedCodeResponse(BaseModel):
    """Schema for widget embed code."""

    widget_id: str
    iframe_code: str
    script_code: str


class WidgetListResponse(BaseModel):
    """Schema for paginated widget list."""

    items: list[WidgetResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool
