"""Japan intelligence endpoints."""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models import (
    Card,
    JPCardInnovation,
    JPNewArchetype,
    JPSetImpact,
    Prediction,
    Tournament,
    TournamentPlacement,
    TranslatedContent,
)
from src.schemas.japan import (
    CardCountDataPoint,
    CardCountEvolution,
    CardCountEvolutionResponse,
    CityLeagueResult,
    JPCardInnovationDetailResponse,
    JPCardInnovationListResponse,
    JPCardInnovationResponse,
    JPContentItem,
    JPContentListResponse,
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


@router.get("/card-count-evolution")
async def get_card_count_evolution(
    db: Annotated[AsyncSession, Depends(get_db)],
    archetype: Annotated[str, Query(description="Archetype name")],
    days: Annotated[
        int, Query(ge=7, le=365, description="Lookback window in days")
    ] = 90,
    top_cards: Annotated[
        int, Query(ge=1, le=30, description="Number of cards to track")
    ] = 10,
) -> CardCountEvolutionResponse:
    """Get card count evolution for an archetype over time.

    Computes how average copies of cards change across weekly buckets,
    based on JP City League tournament placements.
    """
    cutoff_date = date.today() - timedelta(days=days)

    # Fetch JP placements for this archetype with their tournament dates
    query = (
        select(TournamentPlacement, Tournament.date)
        .join(Tournament, TournamentPlacement.tournament_id == Tournament.id)
        .where(
            TournamentPlacement.archetype == archetype,
            Tournament.region == "JP",
            Tournament.best_of == 1,
            Tournament.date >= cutoff_date,
            TournamentPlacement.decklist.isnot(None),
        )
        .order_by(Tournament.date)
    )

    try:
        result = await db.execute(query)
        rows = result.all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching card count evolution: archetype=%s",
            archetype,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to compute card count evolution. Please try again later.",
        ) from None

    if not rows:
        return CardCountEvolutionResponse(
            archetype=archetype,
            cards=[],
            tournaments_analyzed=0,
        )

    # Group placements into weekly buckets and track card counts
    # week_key -> card_id -> list of quantities (0 if not included)
    week_card_counts: dict[date, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    tournament_ids: set[str] = set()
    all_card_ids: set[str] = set()

    for placement, tournament_date in rows:
        tournament_ids.add(str(placement.tournament_id))
        # Bucket by ISO week start (Monday)
        week_start = tournament_date - timedelta(days=tournament_date.weekday())

        # Build card quantity map for this decklist
        deck_cards: dict[str, int] = {}
        for entry in placement.decklist or []:
            if isinstance(entry, dict) and "card_id" in entry:
                card_id = entry["card_id"]
                quantity = int(entry.get("quantity", 1))
                deck_cards[card_id] = deck_cards.get(card_id, 0) + quantity
                all_card_ids.add(card_id)

        # Record counts for all cards seen so far
        for card_id in all_card_ids:
            week_card_counts[week_start][card_id].append(deck_cards.get(card_id, 0))

    # Resolve card names
    card_names: dict[str, str] = {}
    if all_card_ids:
        try:
            card_query = select(Card.id, Card.name).where(
                Card.id.in_(list(all_card_ids))
            )
            card_result = await db.execute(card_query)
            for row in card_result:
                card_names[row.id] = row.name
        except SQLAlchemyError:
            logger.warning("Could not resolve card names", exc_info=True)

    # Compute per-card evolution data
    sorted_weeks = sorted(week_card_counts.keys())
    card_evolutions: dict[str, list[CardCountDataPoint]] = defaultdict(list)

    for week in sorted_weeks:
        for card_id, counts in week_card_counts[week].items():
            total_decks = len(counts)
            included = sum(1 for c in counts if c > 0)
            avg_copies = sum(counts) / total_decks if total_decks > 0 else 0.0

            card_evolutions[card_id].append(
                CardCountDataPoint(
                    snapshot_date=week,
                    avg_copies=round(avg_copies, 2),
                    inclusion_rate=(
                        round(included / total_decks, 4) if total_decks > 0 else 0.0
                    ),
                    sample_size=total_decks,
                )
            )

    # Select top cards by largest absolute change
    card_changes: list[tuple[str, float, float]] = []
    for card_id, data_points in card_evolutions.items():
        if len(data_points) < 2:
            continue
        first_avg = data_points[0].avg_copies
        last_avg = data_points[-1].avg_copies
        total_change = last_avg - first_avg
        card_changes.append((card_id, abs(total_change), total_change))

    card_changes.sort(key=lambda x: x[1], reverse=True)
    top_card_ids = [c[0] for c in card_changes[:top_cards]]

    # If we don't have enough movers, fill with most-included cards
    if len(top_card_ids) < top_cards:
        remaining = top_cards - len(top_card_ids)
        top_set = set(top_card_ids)
        # Sort by latest avg copies descending
        other_cards = [
            (cid, dp[-1].avg_copies)
            for cid, dp in card_evolutions.items()
            if cid not in top_set and dp
        ]
        other_cards.sort(key=lambda x: x[1], reverse=True)
        top_card_ids.extend(c[0] for c in other_cards[:remaining])

    # Build response
    cards: list[CardCountEvolution] = []
    for card_id in top_card_ids:
        data_points = card_evolutions.get(card_id, [])
        first_avg = data_points[0].avg_copies if data_points else 0.0
        last_avg = data_points[-1].avg_copies if data_points else 0.0

        cards.append(
            CardCountEvolution(
                card_id=card_id,
                card_name=card_names.get(card_id, card_id),
                data_points=data_points,
                total_change=round(last_avg - first_avg, 2),
                current_avg=round(last_avg, 2),
            )
        )

    return CardCountEvolutionResponse(
        archetype=archetype,
        cards=cards,
        tournaments_analyzed=len(tournament_ids),
    )


@router.get("/content")
async def list_jp_content(
    db: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[str | None, Query(description="Filter by source name")] = None,
    content_type: Annotated[
        str | None,
        Query(description="Filter by content type"),
    ] = None,
    era: Annotated[str | None, Query(description="Filter by era label")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> JPContentListResponse:
    """Get translated JP content (articles, tier lists).

    Returns translated content from Japanese sources like Pokecabook
    and Pokekameshi, ordered by publication date descending.
    """
    query = select(TranslatedContent).where(
        TranslatedContent.status == "translated",
    )

    if source:
        query = query.where(TranslatedContent.source_name == source)
    if content_type:
        query = query.where(TranslatedContent.content_type == content_type)
    if era:
        query = query.where(TranslatedContent.era_label == era)

    # Order by published_date, fall back to translated_at
    query = query.order_by(
        TranslatedContent.published_date.desc().nulls_last(),
        TranslatedContent.translated_at.desc().nulls_last(),
    ).limit(limit)

    # Count query
    count_query = select(func.count(TranslatedContent.id)).where(
        TranslatedContent.status == "translated",
    )
    if source:
        count_query = count_query.where(TranslatedContent.source_name == source)
    if content_type:
        count_query = count_query.where(TranslatedContent.content_type == content_type)
    if era:
        count_query = count_query.where(TranslatedContent.era_label == era)

    try:
        result = await db.execute(query)
        items = result.scalars().all()
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
    except SQLAlchemyError:
        logger.error(
            "Database error fetching JP content",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("Unable to retrieve JP content. Please try again later."),
        ) from None

    return JPContentListResponse(
        items=[
            JPContentItem(
                id=str(item.id),
                source_url=item.source_url,
                content_type=item.content_type,
                title_en=getattr(item, "title_en", None),
                title_jp=getattr(item, "title_jp", None),
                translated_text=(
                    item.translated_text[:500] if item.translated_text else None
                ),
                published_date=getattr(item, "published_date", None),
                source_name=getattr(item, "source_name", None),
                tags=getattr(item, "tags", None),
                archetype_refs=getattr(item, "archetype_refs", None),
                era_label=getattr(item, "era_label", None),
                review_status=getattr(
                    item,
                    "review_status",
                    "auto_approved",
                ),
                translated_at=item.translated_at,
            )
            for item in items
        ],
        total=total,
    )
