"""Meta snapshot endpoints."""

import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta
from enum import IntEnum
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models import MetaSnapshot, Tournament, TournamentPlacement
from src.schemas import (
    ArchetypeDetailResponse,
    ArchetypeHistoryPoint,
    ArchetypeResponse,
    CardUsageSummary,
    FormatNotes,
    KeyCardResponse,
    MetaHistoryResponse,
    MetaSnapshotResponse,
    SampleDeckResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meta", tags=["meta"])


class BestOf(IntEnum):
    """Match format options."""

    BO1 = 1
    BO3 = 3


# Format notes for Japan BO1
JAPAN_BO1_FORMAT_NOTES = FormatNotes(
    tie_rules="Tie = double loss (both players receive a loss)",
    typical_regions=["JP"],
    notes=(
        "Japan uses Best-of-1 format for most tournaments. "
        "Ties result in double losses, which can significantly impact "
        "archetype viability compared to international BO3 formats."
    ),
)


def _get_format_notes(best_of: int, region: str | None) -> FormatNotes | None:
    """Get format-specific notes based on best_of and region.

    Only Japan (JP) BO1 tournaments have special format notes since
    international major events are all Best-of-3.
    """
    if best_of == 1 and region == "JP":
        return JAPAN_BO1_FORMAT_NOTES
    return None


def _snapshot_to_response(
    snapshot: MetaSnapshot,
    include_format_notes: bool = True,
) -> MetaSnapshotResponse:
    """Convert a MetaSnapshot model to response schema."""
    archetype_breakdown = [
        ArchetypeResponse(name=name, share=share)
        for name, share in (snapshot.archetype_shares or {}).items()
    ]

    card_usage = []
    if snapshot.card_usage:
        for card_id, usage_data in snapshot.card_usage.items():
            card_usage.append(
                CardUsageSummary(
                    card_id=card_id,
                    inclusion_rate=usage_data.get("inclusion_rate", 0.0),
                    avg_copies=usage_data.get("avg_count", 0.0),
                )
            )

    format_notes = None
    if include_format_notes:
        format_notes = _get_format_notes(snapshot.best_of, snapshot.region)

    return MetaSnapshotResponse(
        snapshot_date=snapshot.snapshot_date,
        region=snapshot.region,
        format=snapshot.format,  # type: ignore[arg-type]
        best_of=snapshot.best_of,
        archetype_breakdown=archetype_breakdown,
        card_usage=card_usage,
        sample_size=snapshot.sample_size,
        tournaments_included=snapshot.tournaments_included,
        format_notes=format_notes,
    )


@router.get("/current")
async def get_current_meta(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: Annotated[
        str | None,
        Query(description="Region filter (NA, EU, JP, etc.) or null for global"),
    ] = None,
    format: Annotated[
        Literal["standard", "expanded"],
        Query(description="Game format"),
    ] = "standard",
    best_of: Annotated[
        BestOf,
        Query(description="Match format (1 for Japan BO1, 3 for international BO3)"),
    ] = BestOf.BO3,
) -> MetaSnapshotResponse:
    """Get the current (latest) meta snapshot.

    Returns the most recent meta snapshot matching the specified filters.
    Defaults to global region, standard format, and BO3.
    """
    query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
    )

    if region is None:
        query = query.where(MetaSnapshot.region.is_(None))
    else:
        query = query.where(MetaSnapshot.region == region)

    query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(1)

    try:
        result = await db.execute(query)
        snapshot = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching current meta: region=%s, format=%s, best_of=%s",
            region,
            format,
            best_of,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve meta snapshot. Please try again later.",
        ) from None

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No meta snapshot found for region={region or 'global'}, "
                f"format={format}, best_of={best_of}"
            ),
        )

    return _snapshot_to_response(snapshot)


@router.get("/history")
async def get_meta_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: Annotated[
        str | None,
        Query(description="Region filter (NA, EU, JP, etc.) or null for global"),
    ] = None,
    format: Annotated[
        Literal["standard", "expanded"],
        Query(description="Game format"),
    ] = "standard",
    best_of: Annotated[
        BestOf,
        Query(description="Match format (1 for Japan BO1, 3 for international BO3)"),
    ] = BestOf.BO3,
    days: Annotated[
        int,
        Query(ge=1, le=365, description="Number of days of history to return"),
    ] = 90,
) -> MetaHistoryResponse:
    """Get historical meta snapshots.

    Returns meta snapshots within the specified date range,
    ordered by snapshot date descending (newest first).
    """
    start_date = date.today() - timedelta(days=days)

    query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
        MetaSnapshot.snapshot_date >= start_date,
    )

    if region is None:
        query = query.where(MetaSnapshot.region.is_(None))
    else:
        query = query.where(MetaSnapshot.region == region)

    query = query.order_by(MetaSnapshot.snapshot_date.desc())

    try:
        result = await db.execute(query)
        snapshots = result.scalars().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching meta history: "
            "region=%s, format=%s, best_of=%s, days=%s",
            region,
            format,
            best_of,
            days,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve meta history. Please try again later.",
        ) from None

    return MetaHistoryResponse(snapshots=[_snapshot_to_response(s) for s in snapshots])


@router.get("/archetypes")
async def list_archetypes(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: Annotated[
        str | None,
        Query(description="Region filter (NA, EU, JP, etc.) or null for global"),
    ] = None,
    format: Annotated[
        Literal["standard", "expanded"],
        Query(description="Game format"),
    ] = "standard",
    best_of: Annotated[
        BestOf,
        Query(description="Match format (1 for Japan BO1, 3 for international BO3)"),
    ] = BestOf.BO3,
) -> list[ArchetypeResponse]:
    """List all archetypes from the current meta snapshot.

    Returns archetypes with their current meta share percentages,
    sorted by share descending (most popular first).
    """
    query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
    )

    if region is None:
        query = query.where(MetaSnapshot.region.is_(None))
    else:
        query = query.where(MetaSnapshot.region == region)

    query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(1)

    try:
        result = await db.execute(query)
        snapshot = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching archetypes: region=%s, format=%s, best_of=%s",
            region,
            format,
            best_of,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve archetypes. Please try again later.",
        ) from None

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No meta snapshot found for region={region or 'global'}, "
                f"format={format}, best_of={best_of}"
            ),
        )

    archetypes = [
        ArchetypeResponse(name=name, share=share)
        for name, share in (snapshot.archetype_shares or {}).items()
    ]

    # Already sorted by share from compute_meta_snapshot, but ensure order
    archetypes.sort(key=lambda a: a.share, reverse=True)

    return archetypes


@router.get("/archetypes/{name}")
async def get_archetype_detail(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    region: Annotated[
        str | None,
        Query(description="Region filter (NA, EU, JP, etc.) or null for global"),
    ] = None,
    format: Annotated[
        Literal["standard", "expanded"],
        Query(description="Game format"),
    ] = "standard",
    best_of: Annotated[
        BestOf,
        Query(description="Match format (1 for Japan BO1, 3 for international BO3)"),
    ] = BestOf.BO3,
    days: Annotated[
        int,
        Query(ge=1, le=365, description="Number of days of history to return"),
    ] = 90,
) -> ArchetypeDetailResponse:
    """Get detailed information for a specific archetype.

    Returns:
    - Current meta share
    - Historical share over time
    - Key cards with inclusion rates
    - Sample decklists from recent tournaments
    """
    start_date = date.today() - timedelta(days=days)

    # Get historical snapshots for archetype share over time
    snapshot_query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
        MetaSnapshot.snapshot_date >= start_date,
    )

    if region is None:
        snapshot_query = snapshot_query.where(MetaSnapshot.region.is_(None))
    else:
        snapshot_query = snapshot_query.where(MetaSnapshot.region == region)

    snapshot_query = snapshot_query.order_by(MetaSnapshot.snapshot_date.desc())

    try:
        result = await db.execute(snapshot_query)
        snapshots = result.scalars().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching archetype history: name=%s, region=%s, format=%s",
            name,
            region,
            format,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve archetype details. Please try again later.",
        ) from None

    # Build history from snapshots
    history: list[ArchetypeHistoryPoint] = []
    current_share = 0.0
    found = False

    for snapshot in snapshots:
        archetype_shares = snapshot.archetype_shares or {}
        if name in archetype_shares:
            found = True
            share = archetype_shares[name]
            history.append(
                ArchetypeHistoryPoint(
                    snapshot_date=snapshot.snapshot_date,
                    share=share,
                    sample_size=snapshot.sample_size,
                )
            )
            if not current_share and history:
                current_share = share

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archetype '{name}' not found in meta snapshots",
        )

    # Get recent tournament placements for this archetype to compute key cards
    placement_query = (
        select(TournamentPlacement)
        .join(Tournament)
        .where(
            TournamentPlacement.archetype == name,
            Tournament.format == format,
            Tournament.best_of == best_of,
            Tournament.date >= start_date,
        )
    )

    if region:
        placement_query = placement_query.where(Tournament.region == region)

    placement_query = placement_query.order_by(
        TournamentPlacement.placement.asc()
    ).limit(100)

    try:
        placement_result = await db.execute(placement_query)
        placements = placement_result.scalars().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching archetype placements: name=%s",
            name,
            exc_info=True,
        )
        placements = []

    # Compute key cards from placements with decklists
    key_cards = _compute_key_cards(placements)

    # Build sample decks from top placements
    sample_decks = await _build_sample_decks(placements[:10], db)

    return ArchetypeDetailResponse(
        name=name,
        current_share=current_share,
        history=history,
        key_cards=key_cards,
        sample_decks=sample_decks,
    )


def _compute_key_cards(
    placements: Sequence[TournamentPlacement],
) -> list[KeyCardResponse]:
    """Compute key cards from tournament placements."""
    placements_with_lists = [p for p in placements if p.decklist]

    if not placements_with_lists:
        return []

    total = len(placements_with_lists)
    card_appearances: dict[str, int] = defaultdict(int)
    card_total_count: dict[str, int] = defaultdict(int)

    for placement in placements_with_lists:
        seen_cards: set[str] = set()
        for card_entry in placement.decklist or []:
            if not isinstance(card_entry, dict):
                continue

            card_id = card_entry.get("card_id", "")
            if not card_id:
                continue

            try:
                quantity = int(card_entry.get("quantity", 1))
                if quantity < 1:
                    continue
            except (TypeError, ValueError):
                continue

            if card_id not in seen_cards:
                card_appearances[card_id] += 1
                seen_cards.add(card_id)

            card_total_count[card_id] += quantity

    key_cards = []
    for card_id in card_appearances:
        inclusion_rate = card_appearances[card_id] / total
        avg_copies = card_total_count[card_id] / card_appearances[card_id]
        key_cards.append(
            KeyCardResponse(
                card_id=card_id,
                inclusion_rate=round(inclusion_rate, 4),
                avg_copies=round(avg_copies, 2),
            )
        )

    # Sort by inclusion rate descending
    key_cards.sort(key=lambda c: c.inclusion_rate, reverse=True)
    return key_cards[:20]  # Return top 20 key cards


async def _build_sample_decks(
    placements: Sequence[TournamentPlacement],
    db: AsyncSession,
) -> list[SampleDeckResponse]:
    """Build sample deck responses from tournament placements."""
    sample_decks: list[SampleDeckResponse] = []

    # Get tournament info for placements
    tournament_ids = [p.tournament_id for p in placements]
    if tournament_ids:
        try:
            tournament_query = select(Tournament).where(
                Tournament.id.in_(tournament_ids)
            )
            result = await db.execute(tournament_query)
            tournaments = {t.id: t for t in result.scalars().all()}
        except SQLAlchemyError:
            tournaments = {}
    else:
        tournaments = {}

    for placement in placements:
        if not placement.decklist:
            continue

        tournament = tournaments.get(placement.tournament_id)
        sample_decks.append(
            SampleDeckResponse(
                deck_id=str(placement.id),
                tournament_name=tournament.name if tournament else None,
                placement=placement.placement,
                player_name=placement.player_name,
            )
        )

    return sample_decks
