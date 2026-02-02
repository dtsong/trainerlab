"""Lab Note Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Valid lab note types
LabNoteType = Literal[
    "weekly_report",
    "jp_dispatch",
    "set_analysis",
    "rotation_preview",
    "tournament_recap",
    "tournament_preview",
    "archetype_evolution",
]


class RelatedContent(BaseModel):
    """Related content references."""

    model_config = ConfigDict(from_attributes=True)

    archetypes: list[str] = Field(
        default_factory=list, description="Related archetype IDs"
    )
    cards: list[str] = Field(default_factory=list, description="Related card IDs")
    sets: list[str] = Field(default_factory=list, description="Related set codes")


class LabNoteCreate(BaseModel):
    """Request schema for creating a lab note."""

    slug: str = Field(
        min_length=1,
        max_length=255,
        description="URL slug (must be unique)",
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    note_type: LabNoteType = Field(description="Type of lab note")
    title: str = Field(min_length=1, max_length=500, description="Title")
    summary: str | None = Field(
        default=None, max_length=1000, description="Short summary for previews"
    )
    content: str = Field(min_length=1, description="Markdown content")
    author_name: str | None = Field(
        default=None, max_length=255, description="Author display name"
    )
    is_published: bool = Field(default=False, description="Publish immediately")
    meta_description: str | None = Field(
        default=None, max_length=300, description="SEO meta description"
    )
    featured_image_url: str | None = Field(
        default=None, max_length=500, description="Featured image URL"
    )
    tags: list[str] | None = Field(default=None, description="Tags for filtering")
    related_content: RelatedContent | None = Field(
        default=None, description="Related content references"
    )
    is_premium: bool = Field(default=False, description="Premium content flag")


class LabNoteUpdate(BaseModel):
    """Request schema for updating a lab note."""

    title: str | None = Field(
        default=None, min_length=1, max_length=500, description="Title"
    )
    summary: str | None = Field(
        default=None, max_length=1000, description="Short summary"
    )
    content: str | None = Field(default=None, min_length=1, description="Content")
    author_name: str | None = Field(default=None, max_length=255, description="Author")
    is_published: bool | None = Field(default=None, description="Published status")
    meta_description: str | None = Field(default=None, max_length=300)
    featured_image_url: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, description="Tags")
    related_content: RelatedContent | None = Field(default=None)
    is_premium: bool | None = Field(default=None, description="Premium flag")


class LabNoteSummaryResponse(BaseModel):
    """Summary response for lab note listings."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Lab note ID (UUID)")
    slug: str = Field(description="URL slug")
    note_type: LabNoteType = Field(description="Type of lab note")
    title: str = Field(description="Title")
    summary: str | None = Field(default=None, description="Short summary")
    author_name: str | None = Field(default=None, description="Author name")
    is_published: bool = Field(description="Published status")
    published_at: datetime | None = Field(default=None, description="Publish date")
    featured_image_url: str | None = Field(default=None, description="Featured image")
    tags: list[str] | None = Field(default=None, description="Tags")
    is_premium: bool = Field(description="Premium content flag")
    created_at: datetime = Field(description="Creation date")


class LabNoteResponse(BaseModel):
    """Full response for a single lab note."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Lab note ID (UUID)")
    slug: str = Field(description="URL slug")
    note_type: LabNoteType = Field(description="Type of lab note")
    title: str = Field(description="Title")
    summary: str | None = Field(default=None, description="Short summary")
    content: str = Field(description="Markdown content")
    author_name: str | None = Field(default=None, description="Author name")
    is_published: bool = Field(description="Published status")
    published_at: datetime | None = Field(default=None, description="Publish date")
    meta_description: str | None = Field(default=None, description="SEO description")
    featured_image_url: str | None = Field(default=None, description="Featured image")
    tags: list[str] | None = Field(default=None, description="Tags")
    related_content: RelatedContent | None = Field(default=None)
    is_premium: bool = Field(description="Premium content flag")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")


class LabNoteListResponse(BaseModel):
    """Paginated list of lab notes."""

    model_config = ConfigDict(from_attributes=True)

    items: list[LabNoteSummaryResponse] = Field(description="Lab notes")
    total: int = Field(description="Total count")
    page: int = Field(description="Current page")
    limit: int = Field(description="Page size")
    has_next: bool = Field(description="More pages available")
    has_prev: bool = Field(description="Previous pages available")
