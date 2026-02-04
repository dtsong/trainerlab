"""Translation API endpoints.

Public endpoints for JP adoption rates and unreleased cards.
Admin endpoints for managing translations and glossary.
"""

import logging
from datetime import date, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.database import get_db
from src.dependencies.auth import CurrentUser
from src.models.jp_card_adoption_rate import JPCardAdoptionRate
from src.models.jp_unreleased_card import JPUnreleasedCard
from src.models.translated_content import TranslatedContent
from src.models.translation_term_override import TranslationTermOverride
from src.models.user import User
from src.schemas.translation import (
    GlossaryTermCreateRequest,
    GlossaryTermOverrideListResponse,
    GlossaryTermOverrideResponse,
    JPAdoptionRateListResponse,
    JPAdoptionRateResponse,
    JPUnreleasedCardListResponse,
    JPUnreleasedCardResponse,
    SubmitTranslationRequest,
    TranslatedContentListResponse,
    TranslatedContentResponse,
    UpdateTranslationRequest,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["translations"])


def _is_admin(user: User) -> bool:
    """Check if user is an admin."""
    admin_emails = settings.admin_emails.split(",") if settings.admin_emails else []
    return user.email in admin_emails


def _require_admin(user: User) -> None:
    """Raise 403 if user is not an admin."""
    if not _is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


# Public endpoints


@router.get("/japan/adoption-rates", response_model=JPAdoptionRateListResponse)
async def get_jp_adoption_rates(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    archetype: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> JPAdoptionRateListResponse:
    """Get JP card adoption rates.

    Returns recent card adoption rate data from JP meta sources.
    """
    cutoff = date.today() - timedelta(days=days)

    query = select(JPCardAdoptionRate).where(
        JPCardAdoptionRate.period_end >= cutoff
    )

    if archetype:
        query = query.where(JPCardAdoptionRate.archetype_context == archetype)

    query = query.order_by(
        JPCardAdoptionRate.inclusion_rate.desc()
    ).limit(limit)

    result = await db.execute(query)
    rates = result.scalars().all()

    count_query = select(func.count()).select_from(JPCardAdoptionRate).where(
        JPCardAdoptionRate.period_end >= cutoff
    )
    if archetype:
        count_query = count_query.where(
            JPCardAdoptionRate.archetype_context == archetype
        )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return JPAdoptionRateListResponse(
        rates=[
            JPAdoptionRateResponse(
                id=str(r.id),
                card_id=r.card_id,
                card_name_jp=r.card_name_jp,
                card_name_en=r.card_name_en,
                inclusion_rate=r.inclusion_rate,
                avg_copies=r.avg_copies,
                archetype_context=r.archetype_context,
                period_start=r.period_start.isoformat(),
                period_end=r.period_end.isoformat(),
                source=r.source,
            )
            for r in rates
        ],
        total=total,
    )


@router.get("/japan/upcoming-cards", response_model=JPUnreleasedCardListResponse)
async def get_jp_upcoming_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    include_released: Annotated[bool, Query()] = False,
    min_impact: Annotated[int, Query(ge=1, le=5)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> JPUnreleasedCardListResponse:
    """Get JP cards not yet released internationally.

    Returns cards that are legal in JP but not yet in EN format.
    """
    query = select(JPUnreleasedCard)

    if not include_released:
        query = query.where(JPUnreleasedCard.is_released == False)  # noqa: E712

    query = query.where(JPUnreleasedCard.competitive_impact >= min_impact)
    query = query.order_by(JPUnreleasedCard.competitive_impact.desc()).limit(limit)

    result = await db.execute(query)
    cards = result.scalars().all()

    count_query = select(func.count()).select_from(JPUnreleasedCard)
    if not include_released:
        count_query = count_query.where(JPUnreleasedCard.is_released == False)  # noqa: E712
    count_query = count_query.where(JPUnreleasedCard.competitive_impact >= min_impact)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return JPUnreleasedCardListResponse(
        cards=[
            JPUnreleasedCardResponse(
                id=str(c.id),
                jp_card_id=c.jp_card_id,
                jp_set_id=c.jp_set_id,
                name_jp=c.name_jp,
                name_en=c.name_en,
                card_type=c.card_type,
                competitive_impact=c.competitive_impact,
                affected_archetypes=list(c.affected_archetypes)
                if c.affected_archetypes
                else None,
                notes=c.notes,
                expected_release_set=c.expected_release_set,
                is_released=c.is_released,
            )
            for c in cards
        ],
        total=total,
    )


# Admin endpoints


@router.get("/admin/translations", response_model=TranslatedContentListResponse)
async def get_admin_translations(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
    content_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TranslatedContentListResponse:
    """Get translation queue (admin only)."""
    _require_admin(user)

    query = select(TranslatedContent)

    if status_filter:
        query = query.where(TranslatedContent.status == status_filter)
    if content_type:
        query = query.where(TranslatedContent.content_type == content_type)

    query = query.order_by(TranslatedContent.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    content = result.scalars().all()

    count_query = select(func.count()).select_from(TranslatedContent)
    if status_filter:
        count_query = count_query.where(TranslatedContent.status == status_filter)
    if content_type:
        count_query = count_query.where(TranslatedContent.content_type == content_type)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return TranslatedContentListResponse(
        content=[
            TranslatedContentResponse(
                id=str(c.id),
                source_id=c.source_id,
                source_url=c.source_url,
                content_type=c.content_type,
                original_text=c.original_text,
                translated_text=c.translated_text,
                status=c.status,
                translated_at=c.translated_at,
                uncertainties=list(c.uncertainties) if c.uncertainties else None,
            )
            for c in content
        ],
        total=total,
    )


@router.post("/admin/translations", response_model=TranslatedContentResponse)
async def submit_translation(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: SubmitTranslationRequest,
) -> TranslatedContentResponse:
    """Submit a URL for translation (admin only)."""
    _require_admin(user)

    try:
        existing_query = select(TranslatedContent).where(
            TranslatedContent.source_url == request.url
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            return TranslatedContentResponse(
                id=str(existing.id),
                source_id=existing.source_id,
                source_url=existing.source_url,
                content_type=existing.content_type,
                original_text=existing.original_text,
                translated_text=existing.translated_text,
                status=existing.status,
                translated_at=existing.translated_at,
                uncertainties=list(existing.uncertainties)
                if existing.uncertainties
                else None,
            )

        source_id = f"manual-{uuid4().hex[:8]}"
        new_content = TranslatedContent(
            id=uuid4(),
            source_id=source_id,
            source_url=request.url,
            content_type=request.content_type,
            original_text="",
            status="pending",
        )
        db.add(new_content)
        await db.commit()
        await db.refresh(new_content)

        return TranslatedContentResponse(
            id=str(new_content.id),
            source_id=new_content.source_id,
            source_url=new_content.source_url,
            content_type=new_content.content_type,
            original_text=new_content.original_text,
            translated_text=new_content.translated_text,
            status=new_content.status,
            translated_at=new_content.translated_at,
            uncertainties=None,
        )

    except SQLAlchemyError as e:
        logger.error("Error submitting translation: %s", e)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit translation",
        ) from e


@router.patch("/admin/translations/{id}", response_model=TranslatedContentResponse)
async def update_translation(
    id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: UpdateTranslationRequest,
) -> TranslatedContentResponse:
    """Update a translation (admin only)."""
    _require_admin(user)

    query = select(TranslatedContent).where(TranslatedContent.id == id)
    result = await db.execute(query)
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found",
        )

    try:
        if request.translated_text is not None:
            content.translated_text = request.translated_text
        if request.status is not None:
            content.status = request.status

        await db.commit()
        await db.refresh(content)

        return TranslatedContentResponse(
            id=str(content.id),
            source_id=content.source_id,
            source_url=content.source_url,
            content_type=content.content_type,
            original_text=content.original_text,
            translated_text=content.translated_text,
            status=content.status,
            translated_at=content.translated_at,
            uncertainties=(
                list(content.uncertainties) if content.uncertainties else None
            ),
        )

    except SQLAlchemyError as e:
        logger.error("Error updating translation: %s", e)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update translation",
        ) from e


@router.get(
    "/admin/translations/glossary", response_model=GlossaryTermOverrideListResponse
)
async def get_glossary_overrides(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = True,
) -> GlossaryTermOverrideListResponse:
    """Get glossary term overrides (admin only)."""
    _require_admin(user)

    query = select(TranslationTermOverride)
    if active_only:
        query = query.where(TranslationTermOverride.is_active == True)  # noqa: E712
    query = query.order_by(TranslationTermOverride.term_jp)

    result = await db.execute(query)
    terms = result.scalars().all()

    return GlossaryTermOverrideListResponse(
        terms=[
            GlossaryTermOverrideResponse(
                id=str(t.id),
                term_jp=t.term_jp,
                term_en=t.term_en,
                context=t.context,
                source=t.source,
                is_active=t.is_active,
            )
            for t in terms
        ],
        total=len(terms),
    )


@router.post(
    "/admin/translations/glossary", response_model=GlossaryTermOverrideResponse
)
async def create_glossary_override(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: GlossaryTermCreateRequest,
) -> GlossaryTermOverrideResponse:
    """Create or update a glossary term override (admin only)."""
    _require_admin(user)

    try:
        existing_query = select(TranslationTermOverride).where(
            TranslationTermOverride.term_jp == request.term_jp
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.term_en = request.term_en
            existing.context = request.context
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
            return GlossaryTermOverrideResponse(
                id=str(existing.id),
                term_jp=existing.term_jp,
                term_en=existing.term_en,
                context=existing.context,
                source=existing.source,
                is_active=existing.is_active,
            )

        new_term = TranslationTermOverride(
            id=uuid4(),
            term_jp=request.term_jp,
            term_en=request.term_en,
            context=request.context,
            source="admin",
            is_active=True,
        )
        db.add(new_term)
        await db.commit()
        await db.refresh(new_term)

        return GlossaryTermOverrideResponse(
            id=str(new_term.id),
            term_jp=new_term.term_jp,
            term_en=new_term.term_en,
            context=new_term.context,
            source=new_term.source,
            is_active=new_term.is_active,
        )

    except SQLAlchemyError as e:
        logger.error("Error creating glossary override: %s", e)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create glossary override",
        ) from e
