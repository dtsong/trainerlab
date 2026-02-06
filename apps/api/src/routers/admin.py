"""Admin endpoints for placeholder card and archetype sprite management."""

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.archetype_sprite import ArchetypeSprite
from src.models.placeholder_card import PlaceholderCard
from src.schemas.archetype_sprite import (
    ArchetypeSpriteCreate,
    ArchetypeSpriteListResponse,
    ArchetypeSpriteResponse,
    ArchetypeSpriteUpdate,
)
from src.schemas.placeholder import (
    PlaceholderCardCreate,
    PlaceholderCardResponse,
    PlaceholderCardUpdate,
    PlaceholderListResponse,
    TranslationFetchRequest,
    TranslationFetchResponse,
)
from src.services.archetype_normalizer import ArchetypeNormalizer
from src.services.placeholder_service import PlaceholderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post(
    "/placeholder-cards",
    response_model=PlaceholderCardResponse,
    summary="Create placeholder card",
    description="Manually add a placeholder card with translation data.",
)
async def create_placeholder_card(
    data: PlaceholderCardCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaceholderCardResponse:
    """Create a new placeholder card."""
    service = PlaceholderService(db)

    # Check if placeholder already exists
    result = await db.execute(
        select(PlaceholderCard).where(PlaceholderCard.jp_card_id == data.jp_card_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Placeholder already exists for JP card ID: {data.jp_card_id}",
        )

    placeholder = await service.create_placeholder(
        jp_card_id=data.jp_card_id,
        name_jp=data.name_jp,
        name_en=data.name_en,
        supertype=data.supertype,
        source=data.source,
        subtypes=data.subtypes,
        hp=data.hp,
        types=data.types,
        attacks=data.attacks,
        source_url=data.source_url,
        source_account=data.source_account,
    )

    # Create synthetic mapping
    await service.create_synthetic_mapping(data.jp_card_id, placeholder)

    return PlaceholderCardResponse.model_validate(placeholder)


@router.post(
    "/placeholder-cards/batch",
    response_model=list[PlaceholderCardResponse],
    summary="Batch create placeholder cards",
    description="Bulk import placeholder cards from JSON file.",
)
async def create_placeholder_cards_batch(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlaceholderCardResponse]:
    """Batch create placeholder cards from uploaded JSON file."""
    import json

    content = await file.read()
    data = json.loads(content)

    if "cards" not in data:
        raise HTTPException(
            status_code=400, detail="Invalid file format: missing 'cards' key"
        )

    service = PlaceholderService(db)
    created = []

    for card_data in data["cards"]:
        try:
            # Check if already exists
            result = await db.execute(
                select(PlaceholderCard).where(
                    PlaceholderCard.jp_card_id == card_data["jp_card_id"]
                )
            )
            if result.scalar_one_or_none():
                logger.warning(
                    "Skipping existing placeholder: %s", card_data["jp_card_id"]
                )
                continue

            placeholder = await service.create_placeholder(
                jp_card_id=card_data["jp_card_id"],
                name_jp=card_data["name_jp"],
                name_en=card_data["name_en"],
                supertype=card_data["supertype"],
                source=card_data.get("source", "manual"),
                subtypes=card_data.get("subtypes"),
                hp=card_data.get("hp"),
                types=card_data.get("types"),
                attacks=card_data.get("attacks"),
                source_url=card_data.get("source_url"),
                source_account=card_data.get("source_account"),
            )

            await service.create_synthetic_mapping(card_data["jp_card_id"], placeholder)
            created.append(placeholder)

        except Exception as e:
            logger.error(
                "Error creating placeholder for %s: %s", card_data.get("jp_card_id"), e
            )
            continue

    return [PlaceholderCardResponse.model_validate(p) for p in created]


@router.get(
    "/placeholder-cards",
    response_model=PlaceholderListResponse,
    summary="List placeholder cards",
    description="List all placeholder cards with optional filtering.",
)
async def list_placeholder_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    is_unreleased: bool | None = None,
    set_code: str | None = None,
    source: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> PlaceholderListResponse:
    """List placeholder cards with filtering."""
    query = select(PlaceholderCard)

    if is_unreleased is not None:
        query = query.where(PlaceholderCard.is_unreleased == is_unreleased)

    if set_code:
        query = query.where(PlaceholderCard.set_code == set_code)

    if source:
        query = query.where(PlaceholderCard.source == source)

    # Get total count
    count_result = await db.execute(
        select(PlaceholderCard).from_statement(
            query.with_only_columns(PlaceholderCard.id)
        )
    )
    total = len(count_result.scalars().all())

    # Get paginated results
    query = (
        query.order_by(PlaceholderCard.created_at.desc()).offset(offset).limit(limit)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return PlaceholderListResponse(
        total=total,
        items=[PlaceholderCardResponse.model_validate(item) for item in items],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/placeholder-cards/{placeholder_id}",
    response_model=PlaceholderCardResponse,
    summary="Get placeholder card by ID",
)
async def get_placeholder_card(
    placeholder_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaceholderCardResponse:
    """Get a single placeholder card by ID."""
    result = await db.execute(
        select(PlaceholderCard).where(PlaceholderCard.id == placeholder_id)
    )
    placeholder = result.scalar_one_or_none()

    if not placeholder:
        raise HTTPException(status_code=404, detail="Placeholder card not found")

    return PlaceholderCardResponse.model_validate(placeholder)


@router.patch(
    "/placeholder-cards/{placeholder_id}",
    response_model=PlaceholderCardResponse,
    summary="Update placeholder card",
)
async def update_placeholder_card(
    placeholder_id: UUID,
    data: PlaceholderCardUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaceholderCardResponse:
    """Update a placeholder card."""
    result = await db.execute(
        select(PlaceholderCard).where(PlaceholderCard.id == placeholder_id)
    )
    placeholder = result.scalar_one_or_none()

    if not placeholder:
        raise HTTPException(status_code=404, detail="Placeholder card not found")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(placeholder, field, value)

    await db.commit()
    await db.refresh(placeholder)

    return PlaceholderCardResponse.model_validate(placeholder)


@router.post(
    "/translations/fetch",
    response_model=TranslationFetchResponse,
    summary="Fetch translations from social media",
    description="Use LLM to fetch and parse card translations from X/BlueSky accounts.",
)
async def fetch_translations(
    request: TranslationFetchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TranslationFetchResponse:
    """Fetch card translations from social media using LLM."""
    logger.info(
        "Would fetch translations from accounts: %s since %s",
        request.accounts,
        request.since_date,
    )

    if request.dry_run:
        return TranslationFetchResponse(
            accounts_checked=request.accounts,
            posts_fetched=0,
            translations_parsed=0,
            placeholders_created=0,
            dry_run=True,
        )

    # TODO: Implement LLM translation fetcher
    return TranslationFetchResponse(
        accounts_checked=request.accounts,
        posts_fetched=0,
        translations_parsed=0,
        placeholders_created=0,
        dry_run=request.dry_run,
        message="LLM translation fetcher not yet implemented",
    )


@router.post(
    "/placeholder-cards/{placeholder_id}/mark-released",
    response_model=PlaceholderCardResponse,
    summary="Mark placeholder as released",
    description="Mark a placeholder card as officially released with official card ID.",
)
async def mark_placeholder_released(
    placeholder_id: UUID,
    official_card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaceholderCardResponse:
    """Mark a placeholder card as released with official card ID."""
    service = PlaceholderService(db)

    result = await db.execute(
        select(PlaceholderCard).where(PlaceholderCard.id == placeholder_id)
    )
    placeholder = result.scalar_one_or_none()

    if not placeholder:
        raise HTTPException(status_code=404, detail="Placeholder card not found")

    await service.mark_as_released(
        jp_card_id=placeholder.jp_card_id,
        en_card_id=official_card_id,
    )

    return PlaceholderCardResponse.model_validate(placeholder)


# --- Archetype Sprite endpoints ---


@router.get(
    "/archetype-sprites",
    response_model=ArchetypeSpriteListResponse,
    summary="List archetype sprite mappings",
)
async def list_archetype_sprites(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchetypeSpriteListResponse:
    """List all archetype sprite mappings."""
    result = await db.execute(
        select(ArchetypeSprite).order_by(ArchetypeSprite.sprite_key)
    )
    items = result.scalars().all()
    return ArchetypeSpriteListResponse(
        total=len(items),
        items=[ArchetypeSpriteResponse.model_validate(i) for i in items],
    )


@router.post(
    "/archetype-sprites",
    response_model=ArchetypeSpriteResponse,
    summary="Create archetype sprite mapping",
)
async def create_archetype_sprite(
    data: ArchetypeSpriteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchetypeSpriteResponse:
    """Create a new sprite-key to archetype mapping."""
    existing = await db.execute(
        select(ArchetypeSprite).where(ArchetypeSprite.sprite_key == data.sprite_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Sprite key already exists: {data.sprite_key}",
        )

    sprite = ArchetypeSprite(
        id=uuid4(),
        sprite_key=data.sprite_key,
        archetype_name=data.archetype_name,
        sprite_urls=[],
        pokemon_names=[data.sprite_key],
    )
    db.add(sprite)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Sprite key already exists: {data.sprite_key}",
        ) from None
    await db.refresh(sprite)
    return ArchetypeSpriteResponse.model_validate(sprite)


@router.patch(
    "/archetype-sprites/{sprite_key}",
    response_model=ArchetypeSpriteResponse,
    summary="Update archetype sprite mapping",
)
async def update_archetype_sprite(
    sprite_key: str,
    data: ArchetypeSpriteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchetypeSpriteResponse:
    """Update an existing sprite-key to archetype mapping."""
    result = await db.execute(
        select(ArchetypeSprite).where(ArchetypeSprite.sprite_key == sprite_key)
    )
    sprite = result.scalar_one_or_none()
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite mapping not found")
    sprite.archetype_name = data.archetype_name
    await db.commit()
    await db.refresh(sprite)
    return ArchetypeSpriteResponse.model_validate(sprite)


@router.delete(
    "/archetype-sprites/{sprite_key}",
    summary="Delete archetype sprite mapping",
)
async def delete_archetype_sprite(
    sprite_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Delete a sprite-key to archetype mapping."""
    result = await db.execute(
        select(ArchetypeSprite).where(ArchetypeSprite.sprite_key == sprite_key)
    )
    sprite = result.scalar_one_or_none()
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite mapping not found")
    await db.delete(sprite)
    await db.commit()
    return {"deleted": sprite_key}


@router.post(
    "/archetype-sprites/seed",
    summary="Seed archetype sprites from in-code map",
)
async def seed_archetype_sprites(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Seed the archetype_sprites DB table from SPRITE_ARCHETYPE_MAP."""
    try:
        inserted = await ArchetypeNormalizer.seed_db_sprites(db)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Seed failed due to conflicting data",
        ) from None
    return {"inserted": inserted}
