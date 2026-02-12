"""Public API endpoints with API key authentication.

These endpoints are for third-party integrations and content creators
to programmatically access TrainerLab data.
"""

import logging
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import ApiKeyAuth
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.schemas.public import (
    PublicArchetypeDetail,
    PublicArchetypeShare,
    PublicHomeTeaser,
    PublicJPComparison,
    PublicMetaHistoryPoint,
    PublicMetaHistoryResponse,
    PublicMetaSnapshot,
    PublicTeaserArchetype,
    PublicTournamentListResponse,
    PublicTournamentSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/public", tags=["public-api"])

PUBLIC_TEASER_DELAY_DAYS = 14
PUBLIC_TEASER_TOP_N = 5
PUBLIC_TEASER_MIN_SAMPLE_SIZE = 50
PUBLIC_ROUNDING_STEP = 0.005
PUBLIC_TEASER_LOOKBACK_LIMIT = 30


def _round_share_for_public(share: float) -> float:
    """Round a share to the nearest 0.5 percentage points."""
    rounded = round(share / PUBLIC_ROUNDING_STEP) * PUBLIC_ROUNDING_STEP
    return max(0.0, min(1.0, rounded))


@router.get("/teaser/home")
async def get_home_teaser(
    db: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[Literal["standard", "expanded"], Query()] = "standard",
) -> PublicHomeTeaser:
    """Get delayed aggregated homepage teaser data.

    This endpoint is intentionally unauthenticated and returns only
    delayed, rounded, top-N archetype data.
    """
    cutoff_date = date.today() - timedelta(days=PUBLIC_TEASER_DELAY_DAYS)

    global_query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == 3)
        .where(MetaSnapshot.region.is_(None))
        .where(MetaSnapshot.snapshot_date <= cutoff_date)
        .where(MetaSnapshot.sample_size >= PUBLIC_TEASER_MIN_SAMPLE_SIZE)
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(PUBLIC_TEASER_LOOKBACK_LIMIT)
    )

    jp_query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == 1)
        .where(MetaSnapshot.region == "JP")
        .where(MetaSnapshot.snapshot_date <= cutoff_date)
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(1)
    )

    global_result = await db.execute(global_query)
    global_candidates = list(global_result.scalars().all())
    global_snapshot = next(
        (
            snapshot
            for snapshot in global_candidates
            if snapshot.sample_size >= PUBLIC_TEASER_MIN_SAMPLE_SIZE
            and snapshot.archetype_shares
            and len(snapshot.archetype_shares) > 0
        ),
        None,
    )

    jp_result = await db.execute(jp_query)
    jp_snapshot = jp_result.scalar_one_or_none()

    if not global_snapshot:
        return PublicHomeTeaser(
            snapshot_date=None,
            delay_days=PUBLIC_TEASER_DELAY_DAYS,
            sample_size=0,
            top_archetypes=[],
        )

    jp_map = jp_snapshot.archetype_shares if jp_snapshot else {}
    top_archetypes: list[PublicTeaserArchetype] = []

    sorted_global = sorted(
        global_snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
    )[:PUBLIC_TEASER_TOP_N]

    for name, global_share_raw in sorted_global:
        global_share = _round_share_for_public(float(global_share_raw))

        jp_raw = jp_map.get(name)
        jp_share = (
            _round_share_for_public(float(jp_raw)) if jp_raw is not None else None
        )
        divergence_pp = None
        if jp_share is not None:
            divergence_pp = round((jp_share - global_share) * 100, 1)

        top_archetypes.append(
            PublicTeaserArchetype(
                name=name,
                global_share=global_share,
                jp_share=jp_share,
                divergence_pp=divergence_pp,
            )
        )

    return PublicHomeTeaser(
        snapshot_date=global_snapshot.snapshot_date.isoformat(),
        delay_days=PUBLIC_TEASER_DELAY_DAYS,
        sample_size=global_snapshot.sample_size,
        top_archetypes=top_archetypes,
    )


@router.get("/meta")
async def get_meta_snapshot(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: ApiKeyAuth,
    region: Annotated[
        str | None, Query(description="Region filter (null for global)")
    ] = None,
    format: Annotated[Literal["standard", "expanded"], Query()] = "standard",
    best_of: Annotated[Literal[1, 3], Query()] = 3,
) -> PublicMetaSnapshot:
    """Get current meta snapshot.

    Returns the current meta share distribution for the specified region and format.
    Requires API key authentication.
    """
    query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == best_of)
    )

    if region:
        query = query.where(MetaSnapshot.region == region)
    else:
        query = query.where(MetaSnapshot.region.is_(None))

    query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(1)

    result = await db.execute(query)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        return PublicMetaSnapshot(
            snapshot_date="",
            region=region,
            format=format,
            archetypes=[],
            diversity_index=None,
            sample_size=0,
        )

    # Build archetype list
    sorted_archetypes = sorted(
        snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
    )

    archetypes = []
    for name, share in sorted_archetypes:
        tier = (
            snapshot.tier_assignments.get(name) if snapshot.tier_assignments else None
        )
        trend = snapshot.trends.get(name, {}) if snapshot.trends else {}
        archetypes.append(
            PublicArchetypeShare(
                name=name,
                share=float(share),
                tier=tier,
                trend=trend.get("direction"),
            )
        )

    return PublicMetaSnapshot(
        snapshot_date=snapshot.snapshot_date.isoformat(),
        region=region,
        format=format,
        archetypes=archetypes,
        diversity_index=float(snapshot.diversity_index)
        if snapshot.diversity_index
        else None,
        sample_size=snapshot.sample_size,
    )


@router.get("/meta/history")
async def get_meta_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: ApiKeyAuth,
    region: Annotated[str | None, Query(description="Region filter")] = None,
    format: Annotated[Literal["standard", "expanded"], Query()] = "standard",
    best_of: Annotated[Literal[1, 3], Query()] = 3,
    days: Annotated[int, Query(ge=1, le=90)] = 30,
) -> PublicMetaHistoryResponse:
    """Get meta history over time.

    Returns daily meta snapshots for the specified period.
    Requires API key authentication.
    """
    query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == best_of)
    )

    if region:
        query = query.where(MetaSnapshot.region == region)
    else:
        query = query.where(MetaSnapshot.region.is_(None))

    query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(days)

    result = await db.execute(query)
    snapshots = list(result.scalars().all())

    history = []
    for snapshot in reversed(snapshots):  # Chronological order
        top_archetypes = sorted(
            snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
        )[:10]

        history.append(
            PublicMetaHistoryPoint(
                date=snapshot.snapshot_date.isoformat(),
                archetypes={name: float(share) for name, share in top_archetypes},
                sample_size=snapshot.sample_size,
            )
        )

    return PublicMetaHistoryResponse(
        region=region,
        format=format,
        days=days,
        history=history,
    )


@router.get("/archetypes/{archetype}")
async def get_archetype_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: ApiKeyAuth,
    archetype: str,
    region: Annotated[str | None, Query()] = None,
    format: Annotated[Literal["standard", "expanded"], Query()] = "standard",
    best_of: Annotated[Literal[1, 3], Query()] = 3,
) -> PublicArchetypeDetail:
    """Get detailed archetype information.

    Returns share, tier, and trend data for a specific archetype.
    Requires API key authentication.
    """
    query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == best_of)
    )

    if region:
        query = query.where(MetaSnapshot.region == region)
    else:
        query = query.where(MetaSnapshot.region.is_(None))

    query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(1)

    result = await db.execute(query)
    snapshot = result.scalar_one_or_none()

    if not snapshot or archetype not in snapshot.archetype_shares:
        return PublicArchetypeDetail(
            name=archetype,
            share=0,
            tier=None,
            trend=None,
            rank=None,
            region=region,
            format=format,
        )

    share = float(snapshot.archetype_shares[archetype])
    tier = (
        snapshot.tier_assignments.get(archetype) if snapshot.tier_assignments else None
    )
    trend = snapshot.trends.get(archetype, {}) if snapshot.trends else {}

    # Calculate rank
    sorted_archetypes = sorted(
        snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
    )
    rank = next(
        (i + 1 for i, (name, _) in enumerate(sorted_archetypes) if name == archetype),
        None,
    )

    return PublicArchetypeDetail(
        name=archetype,
        share=share,
        tier=tier,
        trend=trend.get("direction"),
        trend_change=trend.get("change"),
        rank=rank,
        region=region,
        format=format,
        snapshot_date=snapshot.snapshot_date.isoformat(),
    )


@router.get("/tournaments")
async def list_tournaments(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: ApiKeyAuth,
    region: Annotated[str | None, Query()] = None,
    format: Annotated[Literal["standard", "expanded"] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PublicTournamentListResponse:
    """List recent tournaments.

    Returns a paginated list of tournaments with basic metadata.
    Requires API key authentication.
    """
    query = select(Tournament)

    if region:
        query = query.where(Tournament.region == region)
    if format:
        query = query.where(Tournament.format == format)

    query = query.order_by(Tournament.date.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    tournaments = list(result.scalars().all())

    items = []
    for t in tournaments:
        items.append(
            PublicTournamentSummary(
                id=str(t.id),
                name=t.name,
                date=t.date.isoformat() if t.date else None,
                region=t.region,
                format=t.format,
                tier=t.tier,
                participant_count=t.participant_count,
            )
        )

    return PublicTournamentListResponse(
        items=items,
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/japan/comparison")
async def get_jp_comparison(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: ApiKeyAuth,
    format: Annotated[Literal["standard", "expanded"], Query()] = "standard",
    top_n: Annotated[int, Query(ge=1, le=20)] = 10,
) -> PublicJPComparison:
    """Get JP vs EN meta comparison.

    Compares Japan BO1 meta with global BO3 meta.
    Requires API key authentication.
    """
    # Get JP snapshot (BO1)
    jp_query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == 1)
        .where(MetaSnapshot.region == "JP")
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(1)
    )

    jp_result = await db.execute(jp_query)
    jp_snapshot = jp_result.scalar_one_or_none()

    # Get global snapshot (BO3)
    en_query = (
        select(MetaSnapshot)
        .where(MetaSnapshot.format == format)
        .where(MetaSnapshot.best_of == 3)
        .where(MetaSnapshot.region.is_(None))
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(1)
    )

    en_result = await db.execute(en_query)
    en_snapshot = en_result.scalar_one_or_none()

    # Build comparison
    all_archetypes = set()
    if jp_snapshot:
        all_archetypes.update(jp_snapshot.archetype_shares.keys())
    if en_snapshot:
        all_archetypes.update(en_snapshot.archetype_shares.keys())

    comparisons = []
    for archetype in all_archetypes:
        jp_share = (
            float(jp_snapshot.archetype_shares.get(archetype, 0)) if jp_snapshot else 0
        )
        en_share = (
            float(en_snapshot.archetype_shares.get(archetype, 0)) if en_snapshot else 0
        )
        comparisons.append(
            {
                "archetype": archetype,
                "jp_share": jp_share,
                "en_share": en_share,
                "divergence": jp_share - en_share,
            }
        )

    # Sort by max share and take top N
    comparisons.sort(key=lambda x: max(x["jp_share"], x["en_share"]), reverse=True)
    comparisons = comparisons[:top_n]

    return PublicJPComparison(
        format=format,
        jp_date=jp_snapshot.snapshot_date.isoformat() if jp_snapshot else None,
        en_date=en_snapshot.snapshot_date.isoformat() if en_snapshot else None,
        comparisons=comparisons,
    )
