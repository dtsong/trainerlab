"""Data export-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EXPORT_TYPES = Literal[
    "meta_snapshot",
    "meta_history",
    "tournament_results",
    "archetype_evolution",
    "card_usage",
    "jp_data",
]

EXPORT_FORMATS = Literal["csv", "json", "xlsx"]


class ExportCreate(BaseModel):
    """Schema for creating a new export."""

    export_type: EXPORT_TYPES = Field(..., description="Type of data to export")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Export configuration"
    )
    format: EXPORT_FORMATS = Field("json", description="Output format")


class ExportResponse(BaseModel):
    """Schema for export data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    export_type: str
    config: dict[str, Any] | None
    format: str
    status: str
    file_path: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExportDownloadResponse(BaseModel):
    """Schema for export download URL."""

    export_id: UUID
    download_url: str
    expires_in_hours: int = 24


class ExportListResponse(BaseModel):
    """Schema for export list."""

    items: list[ExportResponse]
    total: int
