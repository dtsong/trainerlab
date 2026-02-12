"""Public API schemas with simplified structure."""

from typing import Any

from pydantic import BaseModel, Field


class PublicArchetypeShare(BaseModel):
    """Archetype share for public API."""

    name: str
    share: float = Field(..., ge=0, le=1, description="Share as decimal 0-1")
    tier: str | None = None
    trend: str | None = None


class PublicMetaSnapshot(BaseModel):
    """Simplified meta snapshot for public API."""

    snapshot_date: str
    region: str | None
    format: str
    archetypes: list[PublicArchetypeShare]
    diversity_index: float | None = None
    sample_size: int


class PublicMetaHistoryPoint(BaseModel):
    """Single point in meta history."""

    date: str
    archetypes: dict[str, float]
    sample_size: int


class PublicMetaHistoryResponse(BaseModel):
    """Meta history response for public API."""

    region: str | None
    format: str
    days: int
    history: list[PublicMetaHistoryPoint]


class PublicArchetypeDetail(BaseModel):
    """Detailed archetype information."""

    name: str
    share: float
    tier: str | None = None
    trend: str | None = None
    trend_change: float | None = None
    rank: int | None = None
    region: str | None = None
    format: str
    snapshot_date: str | None = None


class PublicTournamentSummary(BaseModel):
    """Tournament summary for public API."""

    id: str
    name: str
    date: str | None
    region: str | None
    format: str | None
    tier: str | None
    participant_count: int | None


class PublicTournamentListResponse(BaseModel):
    """Tournament list response for public API."""

    items: list[PublicTournamentSummary]
    total: int
    limit: int
    offset: int


class PublicJPComparison(BaseModel):
    """JP vs EN comparison for public API."""

    format: str
    jp_date: str | None
    en_date: str | None
    comparisons: list[dict[str, Any]]


class PublicTeaserArchetype(BaseModel):
    """Archetype teaser row for public homepage."""

    name: str
    global_share: float = Field(..., ge=0, le=1)
    jp_share: float | None = Field(default=None, ge=0, le=1)
    divergence_pp: float | None = None


class PublicHomeTeaser(BaseModel):
    """Delayed aggregated homepage teaser."""

    snapshot_date: str | None
    delay_days: int
    sample_size: int
    top_archetypes: list[PublicTeaserArchetype]


__all__ = [
    "PublicArchetypeDetail",
    "PublicArchetypeShare",
    "PublicJPComparison",
    "PublicHomeTeaser",
    "PublicMetaHistoryPoint",
    "PublicMetaHistoryResponse",
    "PublicMetaSnapshot",
    "PublicTeaserArchetype",
    "PublicTournamentListResponse",
    "PublicTournamentSummary",
]
