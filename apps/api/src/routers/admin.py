"""Admin endpoints for placeholder card and archetype sprite management."""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies.admin import AdminUser
from src.models.archetype_sprite import ArchetypeSprite
from src.models.card import Card
from src.models.jp_card_adoption_rate import JPCardAdoptionRate
from src.models.jp_new_archetype import JPNewArchetype
from src.models.meta_snapshot import MetaSnapshot
from src.models.placeholder_card import PlaceholderCard
from src.models.set import Set
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.models.translated_content import TranslatedContent
from src.models.user import User
from src.schemas.admin_data import (
    DataOverviewResponse,
    MetaSnapshotDetailResponse,
    MetaSnapshotListResponse,
    MetaSnapshotSummary,
    PipelineHealthItem,
    PipelineHealthResponse,
    TableInfo,
)
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


class BetaAccessUpdateRequest(BaseModel):
    """Request to grant or revoke beta access."""

    email: EmailStr


class BetaUserResponse(BaseModel):
    """Beta user admin response model."""

    id: str
    email: str
    display_name: str | None
    is_beta_tester: bool
    is_creator: bool
    created_at: datetime
    updated_at: datetime


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
    if data.archetype_name is not None:
        sprite.archetype_name = data.archetype_name
    if data.display_name is not None:
        sprite.display_name = data.display_name or None
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


# --- Admin Data Dashboard endpoints ---


@router.get(
    "/data/overview",
    response_model=DataOverviewResponse,
    summary="Data overview for admin dashboard",
)
async def get_data_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
) -> DataOverviewResponse:
    """Return row counts and freshness for all major tables."""
    tables: list[TableInfo] = []

    # Tournaments
    t_count = await db.scalar(select(func.count()).select_from(Tournament))
    t_max_date = await db.scalar(select(func.max(Tournament.date)))
    tables.append(
        TableInfo(
            name="tournaments",
            row_count=t_count or 0,
            latest_date=(str(t_max_date) if t_max_date else None),
        )
    )

    # Tournament Placements
    tp_count = await db.scalar(select(func.count()).select_from(TournamentPlacement))
    tables.append(
        TableInfo(
            name="tournament_placements",
            row_count=tp_count or 0,
        )
    )

    # Meta Snapshots
    ms_count = await db.scalar(select(func.count()).select_from(MetaSnapshot))
    ms_max_date = await db.scalar(select(func.max(MetaSnapshot.snapshot_date)))
    ms_regions_result = await db.execute(select(MetaSnapshot.region).distinct())
    ms_regions = [r for (r,) in ms_regions_result.all() if r is not None]
    tables.append(
        TableInfo(
            name="meta_snapshots",
            row_count=ms_count or 0,
            latest_date=(str(ms_max_date) if ms_max_date else None),
            detail=f"regions: {', '.join(ms_regions)}",
        )
    )

    # Cards
    c_count = await db.scalar(select(func.count()).select_from(Card))
    tables.append(TableInfo(name="cards", row_count=c_count or 0))

    # Sets
    s_count = await db.scalar(select(func.count()).select_from(Set))
    tables.append(TableInfo(name="sets", row_count=s_count or 0))

    # Users
    u_count = await db.scalar(select(func.count()).select_from(User))
    tables.append(TableInfo(name="users", row_count=u_count or 0))

    # Archetype Sprites
    as_count = await db.scalar(select(func.count()).select_from(ArchetypeSprite))
    as_with_sprites = await db.scalar(
        select(func.count())
        .select_from(ArchetypeSprite)
        .where(ArchetypeSprite.sprite_urls != None)  # noqa: E711
        .where(ArchetypeSprite.sprite_urls != "[]")
    )
    tables.append(
        TableInfo(
            name="archetype_sprites",
            row_count=as_count or 0,
            detail=(f"{as_with_sprites or 0} with sprite URLs"),
        )
    )

    # JP Card Adoption Rates
    ja_count = await db.scalar(select(func.count()).select_from(JPCardAdoptionRate))
    ja_max_date = await db.scalar(select(func.max(JPCardAdoptionRate.period_end)))
    tables.append(
        TableInfo(
            name="jp_card_adoption_rates",
            row_count=ja_count or 0,
            latest_date=(str(ja_max_date) if ja_max_date else None),
        )
    )

    # JP New Archetypes
    jna_count = await db.scalar(select(func.count()).select_from(JPNewArchetype))
    tables.append(
        TableInfo(
            name="jp_new_archetypes",
            row_count=jna_count or 0,
        )
    )

    return DataOverviewResponse(
        tables=tables,
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/data/meta-snapshots",
    response_model=MetaSnapshotListResponse,
    summary="List meta snapshots",
)
async def list_meta_snapshots(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
    region: str | None = None,
    format: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> MetaSnapshotListResponse:
    """List meta snapshots with optional filtering."""
    query = select(MetaSnapshot)

    if region is not None:
        query = query.where(MetaSnapshot.region == region)
    if format is not None:
        query = query.where(MetaSnapshot.format == format)

    # Total count
    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    # Paginated results
    query = (
        query.order_by(MetaSnapshot.snapshot_date.desc()).offset(offset).limit(limit)
    )
    result = await db.execute(query)
    snapshots = result.scalars().all()

    items = []
    for snap in snapshots:
        archetype_count = len(snap.archetype_shares) if snap.archetype_shares else 0
        items.append(
            MetaSnapshotSummary(
                id=str(snap.id),
                snapshot_date=str(snap.snapshot_date),
                region=snap.region,
                format=snap.format,
                best_of=snap.best_of,
                sample_size=snap.sample_size,
                archetype_count=archetype_count,
                diversity_index=(
                    float(snap.diversity_index)
                    if snap.diversity_index is not None
                    else None
                ),
            )
        )

    return MetaSnapshotListResponse(items=items, total=total)


@router.get(
    "/data/meta-snapshots/{snapshot_id}",
    response_model=MetaSnapshotDetailResponse,
    summary="Get meta snapshot detail",
)
async def get_meta_snapshot_detail(
    snapshot_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
) -> MetaSnapshotDetailResponse:
    """Get full detail for a single meta snapshot."""
    result = await db.execute(
        select(MetaSnapshot).where(MetaSnapshot.id == snapshot_id)
    )
    snap = result.scalar_one_or_none()

    if not snap:
        raise HTTPException(
            status_code=404,
            detail="Meta snapshot not found",
        )

    archetype_count = len(snap.archetype_shares) if snap.archetype_shares else 0

    return MetaSnapshotDetailResponse(
        id=str(snap.id),
        snapshot_date=str(snap.snapshot_date),
        region=snap.region,
        format=snap.format,
        best_of=snap.best_of,
        sample_size=snap.sample_size,
        archetype_count=archetype_count,
        diversity_index=(
            float(snap.diversity_index) if snap.diversity_index is not None else None
        ),
        archetype_shares=snap.archetype_shares,
        tier_assignments=snap.tier_assignments,
        card_usage=snap.card_usage,
        jp_signals=snap.jp_signals,
        trends=snap.trends,
        tournaments_included=snap.tournaments_included,
    )


def _pipeline_status(
    days: int | None,
    healthy_threshold: int,
    stale_threshold: int,
) -> str:
    """Determine pipeline health status from days since last run."""
    if days is None:
        return "critical"
    if days <= healthy_threshold:
        return "healthy"
    if days <= stale_threshold:
        return "stale"
    return "critical"


@router.get(
    "/data/pipeline-health",
    response_model=PipelineHealthResponse,
    summary="Pipeline health status",
)
async def get_pipeline_health(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
) -> PipelineHealthResponse:
    """Check freshness of each data pipeline."""
    today = datetime.now(UTC).date()
    pipelines: list[PipelineHealthItem] = []

    # Meta Compute — max snapshot_date (date column)
    meta_date = await db.scalar(select(func.max(MetaSnapshot.snapshot_date)))
    meta_days = (today - meta_date).days if meta_date else None
    pipelines.append(
        PipelineHealthItem(
            name="Meta Compute",
            status=_pipeline_status(meta_days, 2, 7),
            last_run=(str(meta_date) if meta_date else None),
            days_since_run=meta_days,
        )
    )

    # JP Scrape — max Tournament.date where region='JP'
    jp_date = await db.scalar(
        select(func.max(Tournament.date)).where(Tournament.region == "JP")
    )
    jp_days = (today - jp_date).days if jp_date else None
    pipelines.append(
        PipelineHealthItem(
            name="JP Scrape",
            status=_pipeline_status(jp_days, 7, 14),
            last_run=(str(jp_date) if jp_date else None),
            days_since_run=jp_days,
        )
    )

    # JP Intelligence — max JPNewArchetype.updated_at
    jp_intel_dt = await db.scalar(select(func.max(JPNewArchetype.updated_at)))
    jp_intel_date = jp_intel_dt.date() if jp_intel_dt else None
    jp_intel_days = (today - jp_intel_date).days if jp_intel_date else None
    pipelines.append(
        PipelineHealthItem(
            name="JP Intelligence",
            status=_pipeline_status(jp_intel_days, 7, 14),
            last_run=(str(jp_intel_date) if jp_intel_date else None),
            days_since_run=jp_intel_days,
        )
    )

    # Card Sync — max Card.updated_at (datetime)
    card_dt = await db.scalar(select(func.max(Card.updated_at)))
    card_date = card_dt.date() if card_dt else None
    card_days = (today - card_date).days if card_date else None
    pipelines.append(
        PipelineHealthItem(
            name="Card Sync",
            status=_pipeline_status(card_days, 7, 14),
            last_run=(str(card_date) if card_date else None),
            days_since_run=card_days,
        )
    )

    # JP Adoption Rate — max period_end (date)
    adopt_date = await db.scalar(select(func.max(JPCardAdoptionRate.period_end)))
    adopt_days = (today - adopt_date).days if adopt_date else None
    pipelines.append(
        PipelineHealthItem(
            name="JP Adoption Rate",
            status=_pipeline_status(adopt_days, 14, 30),
            last_run=(str(adopt_date) if adopt_date else None),
            days_since_run=adopt_days,
        )
    )

    # Limitless source freshness — latest tournament date where source='limitless'
    limitless_date = await db.scalar(
        select(func.max(Tournament.date)).where(Tournament.source == "limitless")
    )
    limitless_days = (today - limitless_date).days if limitless_date else None
    pipelines.append(
        PipelineHealthItem(
            name="Limitless Source",
            status=_pipeline_status(limitless_days, 3, 14),
            last_run=(str(limitless_date) if limitless_date else None),
            days_since_run=limitless_days,
        )
    )

    # Events source freshness — latest updated_at by event_source
    rk9_dt = await db.scalar(
        select(func.max(Tournament.updated_at)).where(Tournament.event_source == "rk9")
    )
    rk9_date = rk9_dt.date() if rk9_dt else None
    rk9_days = (today - rk9_date).days if rk9_date else None
    pipelines.append(
        PipelineHealthItem(
            name="RK9 Source",
            status=_pipeline_status(rk9_days, 7, 21),
            last_run=(str(rk9_date) if rk9_date else None),
            days_since_run=rk9_days,
        )
    )

    pokemon_dt = await db.scalar(
        select(func.max(Tournament.updated_at)).where(
            Tournament.event_source == "pokemon.com"
        )
    )
    pokemon_date = pokemon_dt.date() if pokemon_dt else None
    pokemon_days = (today - pokemon_date).days if pokemon_date else None
    pipelines.append(
        PipelineHealthItem(
            name="Pokemon Events Source",
            status=_pipeline_status(pokemon_days, 7, 21),
            last_run=(str(pokemon_date) if pokemon_date else None),
            days_since_run=pokemon_days,
        )
    )

    # Translation source freshness — latest content update by source_name
    pokecabook_dt = await db.scalar(
        select(func.max(TranslatedContent.updated_at)).where(
            func.lower(TranslatedContent.source_name) == "pokecabook"
        )
    )
    pokecabook_date = pokecabook_dt.date() if pokecabook_dt else None
    pokecabook_days = (today - pokecabook_date).days if pokecabook_date else None
    pipelines.append(
        PipelineHealthItem(
            name="Pokecabook Source",
            status=_pipeline_status(pokecabook_days, 7, 21),
            last_run=(str(pokecabook_date) if pokecabook_date else None),
            days_since_run=pokecabook_days,
        )
    )

    pokekameshi_dt = await db.scalar(
        select(func.max(TranslatedContent.updated_at)).where(
            func.lower(TranslatedContent.source_name) == "pokekameshi"
        )
    )
    pokekameshi_date = pokekameshi_dt.date() if pokekameshi_dt else None
    pokekameshi_days = (today - pokekameshi_date).days if pokekameshi_date else None
    pipelines.append(
        PipelineHealthItem(
            name="Pokekameshi Source",
            status=_pipeline_status(pokekameshi_days, 7, 21),
            last_run=(str(pokekameshi_date) if pokekameshi_date else None),
            days_since_run=pokekameshi_days,
        )
    )

    return PipelineHealthResponse(
        pipelines=pipelines,
        checked_at=datetime.now(UTC).isoformat(),
    )


@router.get("/beta-users", response_model=list[BetaUserResponse])
async def list_beta_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
    active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[BetaUserResponse]:
    """List users with optional beta access filtering."""
    query = select(User).order_by(User.created_at.desc())

    if active is not None:
        query = query.where(User.is_beta_tester == active)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return [
        BetaUserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            is_beta_tester=user.is_beta_tester,
            is_creator=user.is_creator,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]


@router.post("/beta-users/grant", response_model=BetaUserResponse)
async def grant_beta_access(
    payload: BetaAccessUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
) -> BetaUserResponse:
    """Grant beta access to a user by email."""
    result = await db.execute(
        select(User).where(func.lower(User.email) == payload.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_beta_tester = True
    await db.commit()
    await db.refresh(user)

    return BetaUserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_beta_tester=user.is_beta_tester,
        is_creator=user.is_creator,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/beta-users/revoke", response_model=BetaUserResponse)
async def revoke_beta_access(
    payload: BetaAccessUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin_user: AdminUser,
) -> BetaUserResponse:
    """Revoke beta access from a user by email."""
    result = await db.execute(
        select(User).where(func.lower(User.email) == payload.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_beta_tester = False
    await db.commit()
    await db.refresh(user)

    return BetaUserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_beta_tester=user.is_beta_tester,
        is_creator=user.is_creator,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
