"""Format and rotation endpoints."""

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models import FormatConfig, RotationImpact
from src.schemas.format import (
    FormatConfigResponse,
    RotatingCard,
    RotationDetails,
    RotationImpactListResponse,
    RotationImpactResponse,
    UpcomingFormatResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["format"])


def _format_to_response(format_config: FormatConfig) -> FormatConfigResponse:
    """Convert a FormatConfig model to response schema."""
    rotation_details = None
    if format_config.rotation_details:
        rotation_details = RotationDetails(
            rotating_out_sets=format_config.rotation_details.get(
                "rotating_out_sets", []
            ),
            new_set=format_config.rotation_details.get("new_set"),
        )

    return FormatConfigResponse(
        id=str(format_config.id),
        name=format_config.name,
        display_name=format_config.display_name,
        legal_sets=list(format_config.legal_sets),
        start_date=format_config.start_date,
        end_date=format_config.end_date,
        is_current=format_config.is_current,
        is_upcoming=format_config.is_upcoming,
        rotation_details=rotation_details,
    )


def _impact_to_response(impact: RotationImpact) -> RotationImpactResponse:
    """Convert a RotationImpact model to response schema."""
    rotating_cards = None
    if impact.rotating_cards:
        rotating_cards = [
            RotatingCard(
                card_name=card.get("card_name", ""),
                card_id=card.get("card_id"),
                count=card.get("count", 1),
                role=card.get("role"),
                replacement=card.get("replacement"),
            )
            for card in impact.rotating_cards
        ]

    return RotationImpactResponse(
        id=str(impact.id),
        format_transition=impact.format_transition,
        archetype_id=impact.archetype_id,
        archetype_name=impact.archetype_name,
        survival_rating=impact.survival_rating,  # type: ignore[arg-type]
        rotating_cards=rotating_cards,
        analysis=impact.analysis,
        jp_evidence=impact.jp_evidence,
        jp_survival_share=impact.jp_survival_share,
    )


@router.get("/format/current")
async def get_current_format(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FormatConfigResponse:
    """Get the current format configuration.

    Returns the format that is currently active (is_current=True).
    """
    query = select(FormatConfig).where(FormatConfig.is_current.is_(True)).limit(1)

    try:
        result = await db.execute(query)
        format_config = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error("Database error fetching current format", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve format configuration. Please try again later.",
        ) from None

    if format_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current format configuration found",
        )

    return _format_to_response(format_config)


@router.get("/format/upcoming")
async def get_upcoming_format(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UpcomingFormatResponse:
    """Get the upcoming format configuration with countdown.

    Returns the next format that will become active (is_upcoming=True)
    along with days until rotation.
    """
    query = (
        select(FormatConfig)
        .where(FormatConfig.is_upcoming.is_(True))
        .order_by(FormatConfig.start_date.asc())
        .limit(1)
    )

    try:
        result = await db.execute(query)
        format_config = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error("Database error fetching upcoming format", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve format configuration. Please try again later.",
        ) from None

    if format_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No upcoming format configuration found",
        )

    if format_config.start_date is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upcoming format has no start date configured",
        )

    today = date.today()
    days_until = (format_config.start_date - today).days
    if days_until < 0:
        days_until = 0

    return UpcomingFormatResponse(
        format=_format_to_response(format_config),
        days_until_rotation=days_until,
        rotation_date=format_config.start_date,
    )


@router.get("/rotation/impact")
async def get_rotation_impact(
    db: Annotated[AsyncSession, Depends(get_db)],
    transition: Annotated[
        str,
        Query(
            description="Format transition (e.g., 'svi-asc-to-tef-por')",
            examples=["svi-asc-to-tef-por"],
        ),
    ],
) -> RotationImpactListResponse:
    """Get rotation impact analysis for all archetypes.

    Returns survival ratings and card loss analysis for each archetype
    affected by the specified format transition.
    """
    query = (
        select(RotationImpact)
        .where(RotationImpact.format_transition == transition)
        .order_by(RotationImpact.archetype_name.asc())
    )

    try:
        result = await db.execute(query)
        impacts = result.scalars().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching rotation impacts: transition=%s",
            transition,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve rotation impact data. Please try again later.",
        ) from None

    return RotationImpactListResponse(
        format_transition=transition,
        impacts=[_impact_to_response(impact) for impact in impacts],
        total_archetypes=len(impacts),
    )


@router.get("/rotation/impact/{archetype_id}")
async def get_archetype_rotation_impact(
    archetype_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    transition: Annotated[
        str | None,
        Query(
            description="Format transition (uses latest if not specified)",
            examples=["svi-asc-to-tef-por"],
        ),
    ] = None,
) -> RotationImpactResponse:
    """Get rotation impact analysis for a specific archetype.

    Returns detailed survival rating, rotating cards, and analysis
    for the specified archetype in the given format transition.
    """
    # If no transition specified, get the latest one
    if transition is None:
        # Get the upcoming format to determine the transition
        upcoming_query = (
            select(FormatConfig)
            .where(FormatConfig.is_upcoming.is_(True))
            .order_by(FormatConfig.start_date.asc())
            .limit(1)
        )
        try:
            upcoming_result = await db.execute(upcoming_query)
            upcoming_format = upcoming_result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error("Database error fetching upcoming format", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to retrieve format configuration.",
            ) from None

        if upcoming_format is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No upcoming format found. Please specify a transition.",
            )

        # Get current format to build transition name
        current_query = (
            select(FormatConfig).where(FormatConfig.is_current.is_(True)).limit(1)
        )
        try:
            current_result = await db.execute(current_query)
            current_format = current_result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error("Database error fetching current format", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to retrieve format configuration.",
            ) from None

        if current_format is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current format found. Please specify a transition.",
            )

        transition = f"{current_format.name}-to-{upcoming_format.name}"

    # Get the specific impact
    query = select(RotationImpact).where(
        RotationImpact.format_transition == transition,
        RotationImpact.archetype_id == archetype_id,
    )

    try:
        result = await db.execute(query)
        impact = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching rotation impact: archetype=%s, transition=%s",
            archetype_id,
            transition,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve rotation impact data. Please try again later.",
        ) from None

    if impact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No rotation impact found for archetype '{archetype_id}' "
            f"in transition '{transition}'",
        )

    return _impact_to_response(impact)
