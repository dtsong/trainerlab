"""Trip planning endpoints for the travel companion."""

import logging
from datetime import date
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_db
from src.dependencies import CurrentUser
from src.models import Tournament
from src.models.trip import Trip, TripEvent
from src.models.user import User
from src.schemas.trip import (
    SharedTripView,
    TripCreate,
    TripDetail,
    TripEventAdd,
    TripEventDetail,
    TripSummary,
    TripUpdate,
)
from src.utils.dates import days_until

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])

MAX_FREE_TRIPS = 5


def _build_trip_event_detail(
    te: TripEvent,
) -> TripEventDetail:
    t = te.tournament
    return TripEventDetail(
        id=str(te.id),
        tournament_id=str(te.tournament_id),
        tournament_name=t.name,
        tournament_date=t.date,
        tournament_region=t.region,
        tournament_city=t.city,
        tournament_status=t.status,
        role=te.role,  # type: ignore[arg-type]
        notes=te.notes,
        days_until=days_until(t.date),
    )


async def _get_trip_or_404(
    trip_id: UUID,
    user: User,
    db: AsyncSession,
) -> Trip:
    """Fetch a trip owned by the user or raise 404."""
    query = (
        select(Trip)
        .options(selectinload(Trip.trip_events).selectinload(TripEvent.tournament))
        .where(Trip.id == trip_id, Trip.user_id == user.id)
    )
    try:
        result = await db.execute(query)
        trip = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching trip: id=%s",
            trip_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve trip.",
        ) from None

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip not found: {trip_id}",
        )
    return trip


def _build_trip_detail(trip: Trip) -> TripDetail:
    events = [
        _build_trip_event_detail(te)
        for te in sorted(
            trip.trip_events,
            key=lambda te: te.tournament.date,
        )
    ]
    return TripDetail(
        id=str(trip.id),
        name=trip.name,
        status=trip.status,  # type: ignore[arg-type]
        visibility=trip.visibility,  # type: ignore[arg-type]
        notes=trip.notes,
        share_token=trip.share_token,
        events=events,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_trip(
    body: TripCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetail:
    """Create a new trip. Free users limited to 5 trips."""
    # Check trip limit for non-beta users
    if not user.is_beta_tester:
        count_query = select(func.count()).where(Trip.user_id == user.id)
        result = await db.execute(count_query)
        count = result.scalar() or 0
        if count >= MAX_FREE_TRIPS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Free users are limited to "
                    f"{MAX_FREE_TRIPS} trips. "
                    "Upgrade to Research Pass for unlimited."
                ),
            )

    trip = Trip(
        id=uuid4(),
        user_id=user.id,
        name=body.name,
        notes=body.notes,
    )
    db.add(trip)
    try:
        await db.commit()
        await db.refresh(trip)
    except SQLAlchemyError:
        await db.rollback()
        logger.error("Database error creating trip", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create trip.",
        ) from None

    # Re-fetch with relationships loaded
    return _build_trip_detail(await _get_trip_or_404(trip.id, user, db))


@router.get("")
async def list_trips(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[TripSummary]:
    """List the current user's trips."""
    query = (
        select(Trip)
        .options(selectinload(Trip.trip_events).selectinload(TripEvent.tournament))
        .where(Trip.user_id == user.id)
        .order_by(Trip.created_at.desc())
    )

    try:
        result = await db.execute(query)
        trips = result.scalars().unique().all()
    except SQLAlchemyError:
        logger.error("Database error listing trips", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve trips.",
        ) from None

    items: list[TripSummary] = []
    for trip in trips:
        future_events = [
            te for te in trip.trip_events if te.tournament.date >= date.today()
        ]
        next_event_date = (
            min(te.tournament.date for te in future_events) if future_events else None
        )
        items.append(
            TripSummary(
                id=str(trip.id),
                name=trip.name,
                status=trip.status,  # type: ignore[arg-type]
                event_count=len(trip.trip_events),
                next_event_date=next_event_date,
                created_at=trip.created_at,
            )
        )

    return items


@router.get("/shared/{share_token}")
async def get_shared_trip(
    share_token: Annotated[str, Path(min_length=36, max_length=36)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SharedTripView:
    """View a shared trip (public, no auth required)."""
    query = (
        select(Trip)
        .options(selectinload(Trip.trip_events).selectinload(TripEvent.tournament))
        .where(
            Trip.share_token == share_token,
            Trip.visibility == "shared",
        )
    )

    try:
        result = await db.execute(query)
        trip = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching shared trip",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve trip.",
        ) from None

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared trip not found",
        )

    events = [
        _build_trip_event_detail(te)
        for te in sorted(
            trip.trip_events,
            key=lambda te: te.tournament.date,
        )
    ]

    return SharedTripView(
        name=trip.name,
        events=events,
        created_at=trip.created_at,
    )


@router.get("/{trip_id}")
async def get_trip(
    trip_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetail:
    """Get trip detail (owner only)."""
    trip = await _get_trip_or_404(trip_id, user, db)
    return _build_trip_detail(trip)


@router.put("/{trip_id}")
async def update_trip(
    trip_id: UUID,
    body: TripUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetail:
    """Update a trip (owner only)."""
    trip = await _get_trip_or_404(trip_id, user, db)

    if body.name is not None:
        trip.name = body.name
    if "notes" in body.model_fields_set:
        trip.notes = body.notes
    if body.status is not None:
        trip.status = body.status
    if body.visibility is not None:
        trip.visibility = body.visibility

    try:
        await db.commit()
        await db.refresh(trip)
    except SQLAlchemyError:
        await db.rollback()
        logger.error("Database error updating trip", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to update trip.",
        ) from None

    return _build_trip_detail(await _get_trip_or_404(trip.id, user, db))


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a trip (owner only)."""
    trip = await _get_trip_or_404(trip_id, user, db)

    try:
        await db.delete(trip)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.error("Database error deleting trip", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to delete trip.",
        ) from None


@router.post(
    "/{trip_id}/events",
    status_code=status.HTTP_201_CREATED,
)
async def add_event_to_trip(
    trip_id: UUID,
    body: TripEventAdd,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetail:
    """Add an event/tournament to a trip."""
    trip = await _get_trip_or_404(trip_id, user, db)

    # Verify tournament exists
    t_query = select(Tournament).where(Tournament.id == body.tournament_id)
    try:
        t_result = await db.execute(t_query)
        tournament = t_result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error finding tournament",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify event.",
        ) from None

    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Event not found: {body.tournament_id}"),
        )

    trip_event = TripEvent(
        id=uuid4(),
        trip_id=trip.id,
        tournament_id=body.tournament_id,
        role=body.role,
        notes=body.notes,
    )
    db.add(trip_event)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.warning(
            "Duplicate trip event: trip_id=%s tournament_id=%s",
            trip_id,
            body.tournament_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event already added to this trip",
        ) from None
    except SQLAlchemyError:
        await db.rollback()
        logger.error(
            "Database error adding event to trip",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to add event to trip.",
        ) from None

    return _build_trip_detail(await _get_trip_or_404(trip.id, user, db))


@router.delete(
    "/{trip_id}/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_event_from_trip(
    trip_id: UUID,
    event_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove an event from a trip."""
    trip = await _get_trip_or_404(trip_id, user, db)

    # Find the trip event
    te_query = select(TripEvent).where(
        TripEvent.id == event_id,
        TripEvent.trip_id == trip.id,
    )
    try:
        te_result = await db.execute(te_query)
        trip_event = te_result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error finding trip event",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to remove event.",
        ) from None

    if trip_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip event not found: {event_id}",
        )

    try:
        await db.delete(trip_event)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.error(
            "Database error removing trip event",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to remove event.",
        ) from None


@router.post("/{trip_id}/share")
async def share_trip(
    trip_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripDetail:
    """Generate a share link for a trip."""
    trip = await _get_trip_or_404(trip_id, user, db)

    if not trip.share_token:
        trip.share_token = str(uuid4())
    trip.visibility = "shared"

    try:
        await db.commit()
        await db.refresh(trip)
    except SQLAlchemyError:
        await db.rollback()
        logger.error("Database error sharing trip", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to share trip.",
        ) from None

    return _build_trip_detail(await _get_trip_or_404(trip.id, user, db))
