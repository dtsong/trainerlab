"""Evolution API endpoints.

Provides endpoints for evolution timelines, predictions,
articles, and accuracy tracking.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_db
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.evolution_article import EvolutionArticle
from src.models.evolution_article_snapshot import EvolutionArticleSnapshot
from src.models.tournament import Tournament
from src.schemas.evolution import (
    AdaptationResponse,
    EvolutionArticleListItem,
    EvolutionArticleResponse,
    EvolutionSnapshotResponse,
    EvolutionTimelineResponse,
    PredictionAccuracyResponse,
    PredictionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["evolution"])


def _snapshot_to_response(
    snapshot: ArchetypeEvolutionSnapshot,
) -> EvolutionSnapshotResponse:
    """Convert a snapshot model to response schema."""
    adaptations = [
        AdaptationResponse(
            id=a.id,
            type=a.type,
            description=a.description,
            cards_added=a.cards_added,
            cards_removed=a.cards_removed,
            target_archetype=a.target_archetype,
            confidence=a.confidence,
            source=a.source,
        )
        for a in (snapshot.adaptations or [])
    ]

    return EvolutionSnapshotResponse(
        id=snapshot.id,
        archetype=snapshot.archetype,
        tournament_id=snapshot.tournament_id,
        meta_share=snapshot.meta_share,
        top_cut_conversion=snapshot.top_cut_conversion,
        best_placement=snapshot.best_placement,
        deck_count=snapshot.deck_count,
        consensus_list=snapshot.consensus_list,
        meta_context=snapshot.meta_context,
        adaptations=adaptations,
        created_at=snapshot.created_at,
    )


@router.get("/archetypes/{archetype_id}/evolution")
async def get_archetype_evolution(
    archetype_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Maximum number of snapshots"),
    ] = 10,
) -> EvolutionTimelineResponse:
    """Get the evolution timeline for an archetype.

    Returns snapshots ordered by tournament date (most recent first),
    with adaptations included for each snapshot.
    """
    query = (
        select(ArchetypeEvolutionSnapshot)
        .options(selectinload(ArchetypeEvolutionSnapshot.adaptations))
        .join(
            Tournament,
            ArchetypeEvolutionSnapshot.tournament_id == Tournament.id,
        )
        .where(ArchetypeEvolutionSnapshot.archetype == archetype_id)
        .order_by(Tournament.date.desc())
        .limit(limit)
    )

    try:
        result = await db.execute(query)
        snapshots = list(result.scalars().all())
    except SQLAlchemyError:
        logger.error(
            "Database error fetching evolution timeline: archetype=%s",
            archetype_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve evolution timeline.",
        ) from None

    if not snapshots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evolution data found for archetype '{archetype_id}'",
        )

    return EvolutionTimelineResponse(
        archetype=archetype_id,
        snapshots=[_snapshot_to_response(s) for s in snapshots],
    )


@router.get("/archetypes/{archetype_id}/prediction")
async def get_archetype_prediction(
    archetype_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PredictionResponse:
    """Get the current prediction for an archetype.

    Returns the most recent prediction for any upcoming tournament.
    """
    query = (
        select(ArchetypePrediction)
        .where(ArchetypePrediction.archetype_id == archetype_id)
        .order_by(ArchetypePrediction.created_at.desc())
        .limit(1)
    )

    try:
        result = await db.execute(query)
        prediction = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching prediction: archetype=%s",
            archetype_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve prediction.",
        ) from None

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prediction found for archetype '{archetype_id}'",
        )

    return PredictionResponse(
        id=prediction.id,
        archetype_id=prediction.archetype_id,
        target_tournament_id=prediction.target_tournament_id,
        predicted_meta_share=prediction.predicted_meta_share,
        predicted_day2_rate=prediction.predicted_day2_rate,
        predicted_tier=prediction.predicted_tier,
        likely_adaptations=prediction.likely_adaptations,
        confidence=prediction.confidence,
        methodology=prediction.methodology,
        actual_meta_share=prediction.actual_meta_share,
        accuracy_score=prediction.accuracy_score,
        created_at=prediction.created_at,
    )


@router.get("/evolution")
async def list_evolution_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Maximum number of articles"),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of articles to skip"),
    ] = 0,
) -> list[EvolutionArticleListItem]:
    """List published evolution articles.

    Returns articles ordered by publication date (most recent first).
    """
    query = (
        select(EvolutionArticle)
        .where(EvolutionArticle.status == "published")
        .order_by(EvolutionArticle.published_at.desc())
        .offset(offset)
        .limit(limit)
    )

    try:
        result = await db.execute(query)
        articles = list(result.scalars().all())
    except SQLAlchemyError:
        logger.error(
            "Database error fetching evolution articles",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve articles.",
        ) from None

    return [
        EvolutionArticleListItem(
            id=a.id,
            archetype_id=a.archetype_id,
            slug=a.slug,
            title=a.title,
            excerpt=a.excerpt,
            status=a.status,
            is_premium=a.is_premium,
            published_at=a.published_at,
        )
        for a in articles
    ]


@router.get("/evolution/accuracy")
async def get_prediction_accuracy(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum scored predictions to include"),
    ] = 20,
) -> PredictionAccuracyResponse:
    """Get prediction accuracy tracking summary.

    Returns overall accuracy statistics and recent scored predictions.
    """
    try:
        # Get total and scored counts
        total_result = await db.execute(select(func.count(ArchetypePrediction.id)))
        total = total_result.scalar() or 0

        scored_result = await db.execute(
            select(func.count(ArchetypePrediction.id)).where(
                ArchetypePrediction.accuracy_score.is_not(None)
            )
        )
        scored = scored_result.scalar() or 0

        # Get average accuracy
        avg_result = await db.execute(
            select(func.avg(ArchetypePrediction.accuracy_score)).where(
                ArchetypePrediction.accuracy_score.is_not(None)
            )
        )
        avg_accuracy = avg_result.scalar()

        # Get recent scored predictions
        predictions_result = await db.execute(
            select(ArchetypePrediction)
            .where(ArchetypePrediction.accuracy_score.is_not(None))
            .order_by(ArchetypePrediction.created_at.desc())
            .limit(limit)
        )
        predictions = list(predictions_result.scalars().all())

    except SQLAlchemyError:
        logger.error(
            "Database error fetching prediction accuracy",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve prediction accuracy.",
        ) from None

    return PredictionAccuracyResponse(
        total_predictions=total,
        scored_predictions=scored,
        average_accuracy=round(float(avg_accuracy), 4) if avg_accuracy else None,
        predictions=[
            PredictionResponse(
                id=p.id,
                archetype_id=p.archetype_id,
                target_tournament_id=p.target_tournament_id,
                predicted_meta_share=p.predicted_meta_share,
                predicted_day2_rate=p.predicted_day2_rate,
                predicted_tier=p.predicted_tier,
                likely_adaptations=p.likely_adaptations,
                confidence=p.confidence,
                methodology=p.methodology,
                actual_meta_share=p.actual_meta_share,
                accuracy_score=p.accuracy_score,
                created_at=p.created_at,
            )
            for p in predictions
        ],
    )


@router.get("/evolution/{slug}")
async def get_evolution_article(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvolutionArticleResponse:
    """Get a single evolution article by slug.

    Returns the full article with linked snapshots.
    """
    query = (
        select(EvolutionArticle)
        .options(
            selectinload(EvolutionArticle.article_snapshots).selectinload(
                EvolutionArticleSnapshot.snapshot
            )
        )
        .where(EvolutionArticle.slug == slug)
    )

    try:
        result = await db.execute(query)
        article = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching evolution article: slug=%s",
            slug,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve article.",
        ) from None

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{slug}' not found",
        )

    # Increment view count
    article.view_count = (article.view_count or 0) + 1
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()

    # Build snapshot responses from junction table
    snapshot_responses = []
    for link in sorted(article.article_snapshots, key=lambda x: x.position):
        if link.snapshot:
            snapshot_responses.append(
                EvolutionSnapshotResponse(
                    id=link.snapshot.id,
                    archetype=link.snapshot.archetype,
                    tournament_id=link.snapshot.tournament_id,
                    meta_share=link.snapshot.meta_share,
                    top_cut_conversion=link.snapshot.top_cut_conversion,
                    best_placement=link.snapshot.best_placement,
                    deck_count=link.snapshot.deck_count,
                    consensus_list=link.snapshot.consensus_list,
                    meta_context=link.snapshot.meta_context,
                    created_at=link.snapshot.created_at,
                )
            )

    return EvolutionArticleResponse(
        id=article.id,
        archetype_id=article.archetype_id,
        slug=article.slug,
        title=article.title,
        excerpt=article.excerpt,
        introduction=article.introduction,
        conclusion=article.conclusion,
        status=article.status,
        is_premium=article.is_premium,
        published_at=article.published_at,
        view_count=article.view_count,
        share_count=article.share_count,
        snapshots=snapshot_responses,
    )
