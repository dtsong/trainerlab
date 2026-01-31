"""Meta snapshot endpoints."""

from datetime import date, timedelta
from enum import IntEnum
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models import MetaSnapshot
from src.schemas import (
    ArchetypeResponse,
    CardUsageSummary,
    MetaHistoryResponse,
    MetaSnapshotResponse,
)

router = APIRouter(prefix="/api/v1/meta", tags=["meta"])


class BestOf(IntEnum):
    """Match format options."""

    BO1 = 1
    BO3 = 3


def _snapshot_to_response(snapshot: MetaSnapshot) -> MetaSnapshotResponse:
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
                    avg_count=usage_data.get("avg_count", 0.0),
                )
            )

    return MetaSnapshotResponse(
        snapshot_date=snapshot.snapshot_date,
        region=snapshot.region,
        format=snapshot.format,
        best_of=snapshot.best_of,
        archetype_breakdown=archetype_breakdown,
        card_usage=card_usage,
        sample_size=snapshot.sample_size,
        tournaments_included=snapshot.tournaments_included,
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

    result = await db.execute(query)
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No meta snapshot found for the specified filters",
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

    result = await db.execute(query)
    snapshots = result.scalars().all()

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

    result = await db.execute(query)
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return []

    archetypes = [
        ArchetypeResponse(name=name, share=share)
        for name, share in (snapshot.archetype_shares or {}).items()
    ]

    # Already sorted by share from compute_meta_snapshot, but ensure order
    archetypes.sort(key=lambda a: a.share, reverse=True)

    return archetypes
