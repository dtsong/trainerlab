"""Japan intelligence endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models import JPCardInnovation, JPNewArchetype, JPSetImpact, Prediction
from src.schemas.japan import (
    CityLeagueResult,
    JPCardInnovationDetailResponse,
    JPCardInnovationListResponse,
    JPCardInnovationResponse,
    JPNewArchetypeListResponse,
    JPNewArchetypeResponse,
    JPSetImpactListResponse,
    JPSetImpactResponse,
    MetaBreakdown,
    PredictionListResponse,
    PredictionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/japan", tags=["japan"])


def _innovation_to_response(innovation: JPCardInnovation) -> JPCardInnovationResponse:
    """Convert innovation model to response."""
    return JPCardInnovationResponse(
        id=str(innovation.id),
        card_id=innovation.card_id,
        card_name=innovation.card_name,
        card_name_jp=innovation.card_name_jp,
        set_code=innovation.set_code,
        set_release_jp=innovation.set_release_jp,
        set_release_en=innovation.set_release_en,
        is_legal_en=innovation.is_legal_en,
        adoption_rate=float(innovation.adoption_rate),
        adoption_trend=innovation.adoption_trend,  # type: ignore[arg-type]
        archetypes_using=list(innovation.archetypes_using)
        if innovation.archetypes_using
        else None,
        competitive_impact_rating=innovation.competitive_impact_rating,
        sample_size=innovation.sample_size,
    )


def _innovation_to_detail(
    innovation: JPCardInnovation,
) -> JPCardInnovationDetailResponse:
    """Convert innovation model to detail response."""
    return JPCardInnovationDetailResponse(
        id=str(innovation.id),
        card_id=innovation.card_id,
        card_name=innovation.card_name,
        card_name_jp=innovation.card_name_jp,
        set_code=innovation.set_code,
        set_release_jp=innovation.set_release_jp,
        set_release_en=innovation.set_release_en,
        is_legal_en=innovation.is_legal_en,
        adoption_rate=float(innovation.adoption_rate),
        adoption_trend=innovation.adoption_trend,  # type: ignore[arg-type]
        archetypes_using=list(innovation.archetypes_using)
        if innovation.archetypes_using
        else None,
        competitive_impact_rating=innovation.competitive_impact_rating,
        sample_size=innovation.sample_size,
        impact_analysis=innovation.impact_analysis,
    )


def _archetype_to_response(archetype: JPNewArchetype) -> JPNewArchetypeResponse:
    """Convert archetype model to response."""
    city_league_results = None
    if archetype.city_league_results:
        city_league_results = [
            CityLeagueResult(
                tournament=r.get("tournament", ""),
                date=r.get("date", ""),
                placements=r.get("placements", []),
            )
            for r in archetype.city_league_results
        ]

    return JPNewArchetypeResponse(
        id=str(archetype.id),
        archetype_id=archetype.archetype_id,
        name=archetype.name,
        name_jp=archetype.name_jp,
        key_cards=list(archetype.key_cards) if archetype.key_cards else None,
        enabled_by_set=archetype.enabled_by_set,
        jp_meta_share=float(archetype.jp_meta_share),
        jp_trend=archetype.jp_trend,  # type: ignore[arg-type]
        city_league_results=city_league_results,
        estimated_en_legal_date=archetype.estimated_en_legal_date,
        analysis=archetype.analysis,
    )


def _set_impact_to_response(impact: JPSetImpact) -> JPSetImpactResponse:
    """Convert set impact model to response."""
    meta_before = None
    if impact.jp_meta_before:
        meta_before = [
            MetaBreakdown(archetype=k, share=v)
            for k, v in impact.jp_meta_before.items()
        ]

    meta_after = None
    if impact.jp_meta_after:
        meta_after = [
            MetaBreakdown(archetype=k, share=v) for k, v in impact.jp_meta_after.items()
        ]

    return JPSetImpactResponse(
        id=str(impact.id),
        set_code=impact.set_code,
        set_name=impact.set_name,
        jp_release_date=impact.jp_release_date,
        en_release_date=impact.en_release_date,
        jp_meta_before=meta_before,
        jp_meta_after=meta_after,
        key_innovations=list(impact.key_innovations)
        if impact.key_innovations
        else None,
        new_archetypes=list(impact.new_archetypes) if impact.new_archetypes else None,
        analysis=impact.analysis,
    )


def _prediction_to_response(prediction: Prediction) -> PredictionResponse:
    """Convert prediction model to response."""
    return PredictionResponse(
        id=str(prediction.id),
        prediction_text=prediction.prediction_text,
        target_event=prediction.target_event,
        target_date=prediction.target_date,
        created_at=prediction.created_at,
        resolved_at=prediction.resolved_at,
        outcome=prediction.outcome,  # type: ignore[arg-type]
        confidence=prediction.confidence,  # type: ignore[arg-type]
        category=prediction.category,
        reasoning=prediction.reasoning,
        outcome_notes=prediction.outcome_notes,
    )


@router.get("/innovation")
async def list_card_innovations(
    db: Annotated[AsyncSession, Depends(get_db)],
    set_code: Annotated[str | None, Query(description="Filter by set code")] = None,
    en_legal: Annotated[bool | None, Query(description="Filter by EN legality")] = None,
    min_impact: Annotated[
        int | None, Query(ge=1, le=5, description="Min impact rating")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 50,
) -> JPCardInnovationListResponse:
    """Get JP card innovation tracker data.

    Returns cards that are seeing competitive play in Japan,
    ordered by adoption rate descending.
    """
    query = select(JPCardInnovation)

    if set_code:
        query = query.where(JPCardInnovation.set_code == set_code)
    if en_legal is not None:
        query = query.where(JPCardInnovation.is_legal_en == en_legal)
    if min_impact:
        query = query.where(JPCardInnovation.competitive_impact_rating >= min_impact)

    query = query.order_by(JPCardInnovation.adoption_rate.desc()).limit(limit)

    # Get count
    count_query = select(func.count(JPCardInnovation.id))
    if set_code:
        count_query = count_query.where(JPCardInnovation.set_code == set_code)
    if en_legal is not None:
        count_query = count_query.where(JPCardInnovation.is_legal_en == en_legal)
    if min_impact:
        count_query = count_query.where(
            JPCardInnovation.competitive_impact_rating >= min_impact
        )

    try:
        result = await db.execute(query)
        innovations = result.scalars().all()
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
    except SQLAlchemyError:
        logger.error("Database error fetching card innovations", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve card innovations. Please try again later.",
        ) from None

    return JPCardInnovationListResponse(
        items=[_innovation_to_response(i) for i in innovations],
        total=total,
    )


@router.get("/innovation/{card_id}")
async def get_card_innovation_detail(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JPCardInnovationDetailResponse:
    """Get full card innovation analysis (Research Pass content)."""
    query = select(JPCardInnovation).where(JPCardInnovation.card_id == card_id)

    try:
        result = await db.execute(query)
        innovation = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching card innovation: card_id=%s",
            card_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve card innovation. Please try again later.",
        ) from None

    if innovation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card innovation not found: {card_id}",
        )

    return _innovation_to_detail(innovation)


@router.get("/archetypes/new")
async def list_new_archetypes(
    db: Annotated[AsyncSession, Depends(get_db)],
    set_code: Annotated[str | None, Query(description="Filter by enabling set")] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Page size")] = 20,
) -> JPNewArchetypeListResponse:
    """Get JP-only archetypes not yet in EN meta.

    Returns new archetypes ordered by JP meta share descending.
    """
    query = select(JPNewArchetype)

    if set_code:
        query = query.where(JPNewArchetype.enabled_by_set == set_code)

    query = query.order_by(JPNewArchetype.jp_meta_share.desc()).limit(limit)

    # Get count
    count_query = select(func.count(JPNewArchetype.id))
    if set_code:
        count_query = count_query.where(JPNewArchetype.enabled_by_set == set_code)

    try:
        result = await db.execute(query)
        archetypes = result.scalars().all()
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
    except SQLAlchemyError:
        logger.error("Database error fetching new archetypes", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve new archetypes. Please try again later.",
        ) from None

    return JPNewArchetypeListResponse(
        items=[_archetype_to_response(a) for a in archetypes],
        total=total,
    )


@router.get("/set-impact")
async def list_set_impacts(
    db: Annotated[AsyncSession, Depends(get_db)],
    set_code: Annotated[str | None, Query(description="Filter by set code")] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Page size")] = 20,
) -> JPSetImpactListResponse:
    """Get JP set impact history.

    Returns set impacts ordered by JP release date descending (newest first).
    """
    query = select(JPSetImpact)

    if set_code:
        query = query.where(JPSetImpact.set_code == set_code)

    query = query.order_by(JPSetImpact.jp_release_date.desc()).limit(limit)

    # Get count
    count_query = select(func.count(JPSetImpact.id))
    if set_code:
        count_query = count_query.where(JPSetImpact.set_code == set_code)

    try:
        result = await db.execute(query)
        impacts = result.scalars().all()
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
    except SQLAlchemyError:
        logger.error("Database error fetching set impacts", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve set impacts. Please try again later.",
        ) from None

    return JPSetImpactListResponse(
        items=[_set_impact_to_response(i) for i in impacts],
        total=total,
    )


@router.get("/predictions")
async def list_predictions(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    resolved_only: Annotated[
        bool, Query(description="Only show resolved predictions")
    ] = False,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 50,
) -> PredictionListResponse:
    """Get prediction accuracy tracker.

    Returns predictions with accuracy statistics.
    """
    query = select(Prediction)

    if category:
        query = query.where(Prediction.category == category)
    if resolved_only:
        query = query.where(Prediction.resolved_at.isnot(None))

    query = query.order_by(Prediction.created_at.desc()).limit(limit)

    # Get counts for stats
    total_query = select(func.count(Prediction.id))
    resolved_query = select(func.count(Prediction.id)).where(
        Prediction.resolved_at.isnot(None)
    )
    correct_query = select(func.count(Prediction.id)).where(
        Prediction.outcome == "correct"
    )
    partial_query = select(func.count(Prediction.id)).where(
        Prediction.outcome == "partial"
    )
    incorrect_query = select(func.count(Prediction.id)).where(
        Prediction.outcome == "incorrect"
    )

    try:
        result = await db.execute(query)
        predictions = result.scalars().all()

        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        resolved_result = await db.execute(resolved_query)
        resolved = resolved_result.scalar() or 0

        correct_result = await db.execute(correct_query)
        correct = correct_result.scalar() or 0

        partial_result = await db.execute(partial_query)
        partial = partial_result.scalar() or 0

        incorrect_result = await db.execute(incorrect_query)
        incorrect = incorrect_result.scalar() or 0
    except SQLAlchemyError:
        logger.error("Database error fetching predictions", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve predictions. Please try again later.",
        ) from None

    accuracy_rate = None
    if resolved > 0:
        accuracy_rate = round(correct / resolved, 4)

    return PredictionListResponse(
        items=[_prediction_to_response(p) for p in predictions],
        total=total,
        resolved=resolved,
        correct=correct,
        partial=partial,
        incorrect=incorrect,
        accuracy_rate=accuracy_rate,
    )
