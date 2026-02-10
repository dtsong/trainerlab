"""Event Pydantic schemas for the travel companion."""

from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.tournament import (
    ArchetypeMeta,
    GameFormat,
    TopPlacement,
    TournamentTier,
)

EventStatus = Literal[
    "announced",
    "registration_open",
    "registration_closed",
    "active",
    "completed",
]


class EventSummary(BaseModel):
    """Event summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Event/tournament ID")
    name: str = Field(description="Event name")
    date: date_type = Field(description="Event date")
    region: str = Field(description="Region (NA, EU, JP, etc.)")
    country: str | None = Field(default=None, description="Country")
    format: GameFormat = Field(description="Game format")
    tier: TournamentTier | None = Field(default=None, description="Event tier")
    status: EventStatus = Field(description="Lifecycle status")
    city: str | None = Field(default=None, description="City")
    venue_name: str | None = Field(default=None, description="Venue name")
    registration_url: str | None = Field(default=None, description="Registration URL")
    registration_opens_at: datetime | None = Field(
        default=None, description="Registration open time"
    )
    registration_closes_at: datetime | None = Field(
        default=None, description="Registration close time"
    )
    participant_count: int | None = Field(
        default=None, description="Number of participants"
    )
    days_until: int | None = Field(default=None, description="Days until event")


class EventDetail(EventSummary):
    """Full event detail with meta context."""

    venue_address: str | None = Field(default=None, description="Venue address")
    event_source: str | None = Field(default=None, description="Data source")
    source_url: str | None = Field(default=None, description="Source URL")
    best_of: int = Field(default=3, description="Match format")
    top_placements: list[TopPlacement] = Field(
        default_factory=list,
        description="Top placements (if event completed)",
    )
    meta_breakdown: list[ArchetypeMeta] = Field(
        default_factory=list,
        description="Archetype meta breakdown",
    )
