"""Trip Pydantic schemas for the travel companion."""

from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TripCreate(BaseModel):
    """Request to create a new trip."""

    name: str = Field(min_length=1, max_length=255, description="Trip name")
    notes: str | None = Field(default=None, max_length=2000, description="Trip notes")


class TripUpdate(BaseModel):
    """Request to update a trip."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Trip name",
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Trip notes",
    )
    status: Literal["planning", "upcoming", "active", "completed"] | None = Field(
        default=None, description="Trip status"
    )


class TripEventAdd(BaseModel):
    """Request to add an event to a trip."""

    tournament_id: str = Field(description="Tournament/event ID")
    role: Literal["attendee", "competitor", "judge", "spectator"] = Field(
        default="competitor", description="Role at event"
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Notes for this event",
    )


class TripEventDetail(BaseModel):
    """An event within a trip."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Trip event ID")
    tournament_id: str = Field(description="Tournament/event ID")
    tournament_name: str = Field(description="Event name")
    tournament_date: date_type = Field(description="Event date")
    tournament_region: str = Field(description="Region")
    tournament_city: str | None = Field(default=None, description="City")
    tournament_status: str = Field(description="Event status")
    role: str = Field(description="Role at event")
    notes: str | None = Field(default=None, description="Notes")
    days_until: int | None = Field(default=None, description="Days until event")


class TripSummary(BaseModel):
    """Trip summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Trip ID")
    name: str = Field(description="Trip name")
    status: str = Field(description="Trip status")
    event_count: int = Field(description="Number of events")
    next_event_date: date_type | None = Field(
        default=None, description="Date of next upcoming event"
    )
    created_at: datetime = Field(description="Created at")


class TripDetail(BaseModel):
    """Full trip detail."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Trip ID")
    name: str = Field(description="Trip name")
    status: str = Field(description="Trip status")
    visibility: str = Field(description="Visibility")
    notes: str | None = Field(default=None, description="Trip notes")
    share_token: str | None = Field(default=None, description="Share token")
    events: list[TripEventDetail] = Field(
        default_factory=list, description="Events in this trip"
    )
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")


class SharedTripView(BaseModel):
    """Public read-only view of a shared trip."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Trip name")
    events: list[TripEventDetail] = Field(
        default_factory=list, description="Events in this trip"
    )
    created_at: datetime = Field(description="Created at")
