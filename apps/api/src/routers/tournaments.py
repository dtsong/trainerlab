"""Tournament endpoints."""

import logging
from collections import Counter
from datetime import date, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MappedColumn, selectinload

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.models import Card, Tournament, TournamentPlacement
from src.schemas import BestOf, PaginatedResponse, TopPlacement, TournamentSummary
from src.schemas.tournament import (
    ArchetypeMeta,
    DecklistCardResponse,
    DecklistResponse,
    PlacementDetail,
    TournamentDetailResponse,
    TournamentTier,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/tournaments",
    tags=["tournaments"],
    dependencies=[Depends(require_beta)],
)

# Whitelist of sortable columns (prevents SQL injection via dynamic sort)
SORTABLE_COLUMNS: dict[str, MappedColumn] = {  # type: ignore[type-arg]
    "name": Tournament.name,
    "date": Tournament.date,
    "region": Tournament.region,
    "format": Tournament.format,
    "best_of": Tournament.best_of,
    "tier": Tournament.tier,
    "participants": Tournament.participant_count,
}


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
    tier: Annotated[
        TournamentTier | None,
        Query(description="Filter by tier (major, premier, league)"),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(description="Column to sort by"),
    ] = None,
    order: Annotated[
        Literal["asc", "desc"] | None,
        Query(description="Sort direction"),
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
    if tier:
        if tier == "grassroots":
            query = query.where(
                (Tournament.tier != "major") | (Tournament.tier.is_(None))
            )
        else:
            query = query.where(Tournament.tier == tier)

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
            "start_date=%s, end_date=%s, best_of=%s, tier=%s",
            region,
            format,
            start_date,
            end_date,
            best_of,
            tier,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve tournaments. Please try again later.",
        ) from None

    # Apply sorting (default: date descending)
    sort_column = (
        SORTABLE_COLUMNS.get(sort_by, Tournament.date) if sort_by else Tournament.date
    )
    sort_direction = order or "desc"
    if sort_direction == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    try:
        result = await db.execute(query)
        tournaments = result.scalars().unique().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching tournaments: region=%s, format=%s, "
            "start_date=%s, end_date=%s, best_of=%s, tier=%s, page=%s, limit=%s",
            region,
            format,
            start_date,
            end_date,
            best_of,
            tier,
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
                tier=tournament.tier,  # type: ignore[invalid-argument-type]
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


@router.get("/{tournament_id}")
async def get_tournament(
    tournament_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TournamentDetailResponse:
    """Get detailed tournament information.

    Returns full tournament details including all placements and meta breakdown.
    """
    query = (
        select(Tournament)
        .options(selectinload(Tournament.placements))
        .where(Tournament.id == tournament_id)
    )

    try:
        result = await db.execute(query)
        tournament = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching tournament: id=%s",
            tournament_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve tournament. Please try again later.",
        ) from None

    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament not found: {tournament_id}",
        )

    # Sort placements by placement number
    sorted_placements = sorted(
        tournament.placements,
        key=lambda p: p.placement,
    )

    # Compute meta breakdown from placements
    archetype_counts = Counter(p.archetype for p in sorted_placements)
    total_placements = len(sorted_placements)
    meta_breakdown = [
        ArchetypeMeta(
            archetype=archetype,
            count=count,
            share=round(count / total_placements, 4) if total_placements > 0 else 0.0,
        )
        for archetype, count in archetype_counts.most_common()
    ]

    return TournamentDetailResponse(
        id=str(tournament.id),
        name=tournament.name,
        date=tournament.date,
        region=tournament.region,
        country=tournament.country,
        format=tournament.format,  # type: ignore[arg-type]
        best_of=tournament.best_of,  # type: ignore[arg-type]
        tier=tournament.tier,  # type: ignore[arg-type]
        participant_count=tournament.participant_count,
        source=tournament.source,
        source_url=tournament.source_url,
        placements=[
            PlacementDetail(
                id=str(p.id),
                placement=p.placement,
                player_name=p.player_name,
                archetype=p.archetype,
                has_decklist=p.decklist is not None and len(p.decklist) > 0,
            )
            for p in sorted_placements
        ],
        meta_breakdown=meta_breakdown,
    )


@router.get("/{tournament_id}/placements/{placement_id}/decklist")
async def get_placement_decklist(
    tournament_id: UUID,
    placement_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DecklistResponse:
    """Get full decklist for a tournament placement.

    Returns card names resolved from the Card table with supertype grouping.
    """
    query = (
        select(TournamentPlacement)
        .options(selectinload(TournamentPlacement.tournament))
        .where(
            TournamentPlacement.id == placement_id,
            TournamentPlacement.tournament_id == tournament_id,
        )
    )

    try:
        result = await db.execute(query)
        placement = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching placement decklist: "
            "tournament_id=%s, placement_id=%s",
            tournament_id,
            placement_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve decklist. Please try again later.",
        ) from None

    if placement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Placement not found: {placement_id}",
        )

    if not placement.decklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decklist not available for this placement",
        )

    # Collect card IDs from decklist JSONB
    card_ids = [
        entry["card_id"]
        for entry in placement.decklist
        if isinstance(entry, dict) and "card_id" in entry
    ]

    # Resolve card names and supertypes
    card_lookup: dict[str, tuple[str, str | None]] = {}
    if card_ids:
        try:
            card_query = select(Card.id, Card.name, Card.supertype).where(
                Card.id.in_(card_ids)
            )
            card_result = await db.execute(card_query)
            for row in card_result:
                card_lookup[row.id] = (row.name, row.supertype)
        except SQLAlchemyError:
            logger.error(
                "Database error resolving card names for decklist",
                exc_info=True,
            )
            # Continue with card IDs as fallback names

    # Build response cards
    cards: list[DecklistCardResponse] = []
    total_cards = 0
    for entry in placement.decklist:
        if not isinstance(entry, dict) or "card_id" not in entry:
            continue
        card_id = entry["card_id"]
        quantity = int(entry.get("quantity", 1))
        name, supertype = card_lookup.get(card_id, (card_id, None))
        cards.append(
            DecklistCardResponse(
                card_id=card_id,
                card_name=name,
                quantity=quantity,
                supertype=supertype,
            )
        )
        total_cards += quantity

    tournament = placement.tournament
    return DecklistResponse(
        placement_id=str(placement.id),
        player_name=placement.player_name,
        archetype=placement.archetype,
        tournament_name=tournament.name,
        tournament_date=tournament.date,
        source_url=placement.decklist_source,
        cards=cards,
        total_cards=total_cards,
    )
