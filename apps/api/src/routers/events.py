"""Event discovery endpoints for the travel companion."""

import logging
from collections import Counter
from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_db
from src.models import Tournament
from src.schemas import PaginatedResponse
from src.schemas.event import EventDetail, EventSummary
from src.schemas.tournament import (
    ArchetypeMeta,
    GameFormat,
    TopPlacement,
    TournamentTier,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["events"])


def _days_until(event_date: date) -> int | None:
    """Compute days until an event, or None if past."""
    delta = (event_date - date.today()).days
    return delta if delta >= 0 else None


def _build_event_summary(t: Tournament) -> EventSummary:
    return EventSummary(
        id=str(t.id),
        name=t.name,
        date=t.date,
        region=t.region,
        country=t.country,
        format=t.format,  # type: ignore[arg-type]
        tier=t.tier,  # type: ignore[arg-type]
        status=t.status,  # type: ignore[arg-type]
        city=t.city,
        venue_name=t.venue_name,
        registration_url=t.registration_url,
        registration_opens_at=t.registration_opens_at,
        registration_closes_at=t.registration_closes_at,
        participant_count=t.participant_count,
        days_until=_days_until(t.date),
    )


@router.get("")
async def list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: Annotated[
        str | None,
        Query(description="Filter by region"),
    ] = None,
    format: Annotated[
        GameFormat | None,
        Query(description="Filter by game format"),
    ] = None,
    tier: Annotated[
        TournamentTier | None,
        Query(description="Filter by event tier"),
    ] = None,
    status_filter: Annotated[
        str | None,
        Query(
            alias="status",
            description="Filter by status",
        ),
    ] = None,
    include_completed: Annotated[
        bool,
        Query(description="Include completed events"),
    ] = False,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginatedResponse[EventSummary]:
    """List upcoming events with optional filters."""
    query = select(Tournament)

    if not include_completed:
        query = query.where(Tournament.status != "completed")
    if status_filter:
        query = query.where(Tournament.status == status_filter)
    if region:
        query = query.where(Tournament.region == region)
    if format:
        query = query.where(Tournament.format == format)
    if tier:
        query = query.where(Tournament.tier == tier)

    # Count
    count_query = select(func.count()).select_from(
        query.with_only_columns(Tournament.id).subquery()
    )

    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except SQLAlchemyError:
        logger.error("Database error counting events", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve events.",
        ) from None

    # Sort by date ascending (upcoming first)
    query = query.order_by(Tournament.date.asc())

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    try:
        result = await db.execute(query)
        tournaments = result.scalars().unique().all()
    except SQLAlchemyError:
        logger.error("Database error fetching events", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve events.",
        ) from None

    items = [_build_event_summary(t) for t in tournaments]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=offset + len(items) < total,
        has_prev=page > 1,
    )


@router.get("/{event_id}")
async def get_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventDetail:
    """Get detailed event information with meta context."""
    query = (
        select(Tournament)
        .options(selectinload(Tournament.placements))
        .where(Tournament.id == event_id)
    )

    try:
        result = await db.execute(query)
        tournament = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching event: id=%s",
            event_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve event.",
        ) from None

    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}",
        )

    # Compute meta breakdown from placements
    sorted_placements = sorted(tournament.placements, key=lambda p: p.placement)
    archetype_counts = Counter(p.archetype for p in sorted_placements)
    total_placements = len(sorted_placements)
    meta_breakdown = [
        ArchetypeMeta(
            archetype=archetype,
            count=count,
            share=(round(count / total_placements, 4) if total_placements > 0 else 0.0),
        )
        for archetype, count in archetype_counts.most_common()
    ]

    top_placements = [
        TopPlacement(
            placement=p.placement,
            player_name=p.player_name,
            archetype=p.archetype,
        )
        for p in sorted_placements[:8]
    ]

    return EventDetail(
        id=str(tournament.id),
        name=tournament.name,
        date=tournament.date,
        region=tournament.region,
        country=tournament.country,
        format=tournament.format,  # type: ignore[arg-type]
        tier=tournament.tier,  # type: ignore[arg-type]
        status=tournament.status,  # type: ignore[arg-type]
        city=tournament.city,
        venue_name=tournament.venue_name,
        venue_address=tournament.venue_address,
        registration_url=tournament.registration_url,
        registration_opens_at=tournament.registration_opens_at,
        registration_closes_at=tournament.registration_closes_at,
        participant_count=tournament.participant_count,
        days_until=_days_until(tournament.date),
        event_source=tournament.event_source,
        source_url=tournament.source_url,
        best_of=tournament.best_of,
        top_placements=top_placements,
        meta_breakdown=meta_breakdown,
    )


@router.get("/{event_id}/calendar.ics")
async def get_event_calendar(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Download .ics calendar file for an event."""
    query = select(Tournament).where(Tournament.id == event_id)

    try:
        result = await db.execute(query)
        tournament = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching event for calendar: id=%s",
            event_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve event.",
        ) from None

    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}",
        )

    # Build iCalendar content
    now = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    event_date = tournament.date.strftime("%Y%m%d")

    location_parts = []
    if tournament.venue_name:
        location_parts.append(tournament.venue_name)
    if tournament.city:
        location_parts.append(tournament.city)
    if tournament.country:
        location_parts.append(tournament.country)
    location = ", ".join(location_parts)

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//TrainerLab//Events//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{tournament.id}@trainerlab.gg\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART;VALUE=DATE:{event_date}\r\n"
        f"SUMMARY:{tournament.name}\r\n"
    )
    if location:
        ics += f"LOCATION:{location}\r\n"
    if tournament.registration_url:
        ics += f"URL:{tournament.registration_url}\r\n"
    ics += "END:VEVENT\r\nEND:VCALENDAR\r\n"

    filename = f"{tournament.name.replace(' ', '_')}.ics"

    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": (f'attachment; filename="{filename}"')},
    )
