"""Tournament endpoints."""

import logging
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_db
from src.models import Tournament
from src.schemas import BestOf, PaginatedResponse, TopPlacement, TournamentSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meta/tournaments", tags=["tournaments"])


@router.get("")
async def list_tournaments(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: Annotated[
        str | None,
        Query(description="Filter by region (NA, EU, JP, LATAM, OCE)"),
    ] = None,
    format: Annotated[
        Literal["standard", "expanded"] | None,
        Query(description="Filter by game format"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(description="Filter tournaments on or after this date"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="Filter tournaments on or before this date"),
    ] = None,
    best_of: Annotated[
        BestOf | None,
        Query(description="Filter by match format (1 for BO1, 3 for BO3)"),
    ] = None,
    page: Annotated[
        int,
        Query(ge=1, description="Page number"),
    ] = 1,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Items per page"),
    ] = 20,
) -> PaginatedResponse[TournamentSummary]:
    """List tournaments with pagination and filters.

    Returns tournaments ordered by date descending (most recent first).
    Each tournament includes top placements (top 8).
    """
    # Default to last 90 days if no date range specified
    if start_date is None and end_date is None:
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

    # Build base query
    query = select(Tournament).options(selectinload(Tournament.placements))

    if region:
        query = query.where(Tournament.region == region)
    if format:
        query = query.where(Tournament.format == format)
    if start_date:
        query = query.where(Tournament.date >= start_date)
    if end_date:
        query = query.where(Tournament.date <= end_date)
    if best_of:
        query = query.where(Tournament.best_of == best_of)

    # Get total count
    count_query = select(func.count()).select_from(
        query.with_only_columns(Tournament.id).subquery()
    )

    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except SQLAlchemyError:
        logger.error(
            "Database error counting tournaments: region=%s, format=%s, "
            "start_date=%s, end_date=%s, best_of=%s",
            region,
            format,
            start_date,
            end_date,
            best_of,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve tournaments. Please try again later.",
        ) from None

    # Apply pagination
    offset = (page - 1) * limit
    query = query.order_by(Tournament.date.desc()).offset(offset).limit(limit)

    try:
        result = await db.execute(query)
        tournaments = result.scalars().unique().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching tournaments: region=%s, format=%s, "
            "start_date=%s, end_date=%s, best_of=%s, page=%s, limit=%s",
            region,
            format,
            start_date,
            end_date,
            best_of,
            page,
            limit,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve tournaments. Please try again later.",
        ) from None

    # Build response
    items: list[TournamentSummary] = []
    for tournament in tournaments:
        # Get top 8 placements
        top_placements = sorted(
            tournament.placements,
            key=lambda p: p.placement,
        )[:8]

        items.append(
            TournamentSummary(
                id=str(tournament.id),
                name=tournament.name,
                date=tournament.date,
                region=tournament.region,
                country=tournament.country,
                format=tournament.format,  # type: ignore[invalid-argument-type]
                best_of=tournament.best_of,  # type: ignore[invalid-argument-type]
                participant_count=tournament.participant_count,
                top_placements=[
                    TopPlacement(
                        placement=p.placement,
                        player_name=p.player_name,
                        archetype=p.archetype,
                    )
                    for p in top_placements
                ],
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=offset + len(items) < total,
        has_prev=page > 1,
    )
