"""Pipeline health check schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ScrapeHealthDetail(BaseModel):
    """Scrape pipeline health metrics."""

    status: Literal["ok", "stale", "missing"]
    last_scrape_date: str | None = None
    days_since_scrape: int | None = None
    tournament_count_7d: int = 0
    regions: list[str] = []


class MetaHealthDetail(BaseModel):
    """Meta snapshot health metrics."""

    status: Literal["ok", "stale", "missing"]
    latest_snapshot_date: str | None = None
    snapshot_age_days: int | None = None
    regions: list[str] = []


class ArchetypeHealthDetail(BaseModel):
    """Archetype detection health metrics."""

    status: Literal["ok", "degraded", "poor"]
    unknown_rate: float = 0.0
    rogue_rate: float = 0.0
    method_distribution: dict[str, float] = {}
    uncovered_sprite_keys: list[str] = []
    sample_size: int = 0


# Verbose detail schemas (for ?detail=verbose)


class UnknownPlacementDetail(BaseModel):
    """A placement that resolved to 'Unknown'."""

    tournament_url: str | None = None
    sprite_urls: list[str] = []
    raw_archetype: str | None = None
    detection_method: str | None = None


class TextLabelFallbackDetail(BaseModel):
    """A sprite key that missed the sprite map."""

    sprite_key: str
    resolved_archetype: str
    count: int = 1


class MethodTrendDetail(BaseModel):
    """Detection method distribution for a single day."""

    date: str
    sprite_lookup: float = 0.0
    auto_derive: float = 0.0
    signature_card: float = 0.0
    text_label: float = 0.0


class VerboseArchetypeDetail(BaseModel):
    """Extended archetype detail for verbose mode."""

    unknown_placements: list[UnknownPlacementDetail] = []
    text_label_fallbacks: list[TextLabelFallbackDetail] = []
    method_trends: list[MethodTrendDetail] = []


class SourceHealthDetail(BaseModel):
    """Source freshness and failure visibility detail."""

    source: str
    status: Literal["ok", "stale", "missing"]
    last_success_at: str | None = None
    age_days: int | None = None
    failure_reason: str | None = None


class PipelineHealthResponse(BaseModel):
    """Full pipeline health response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    scrape: ScrapeHealthDetail
    meta: MetaHealthDetail
    archetype: ArchetypeHealthDetail
    sources: list[SourceHealthDetail] = []
    checked_at: datetime
    verbose: VerboseArchetypeDetail | None = None
