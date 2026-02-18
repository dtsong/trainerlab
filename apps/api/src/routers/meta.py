"""Meta snapshot endpoints."""

import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.models import MetaSnapshot, Tournament, TournamentPlacement
from src.models.archetype_sprite import ArchetypeSprite
from src.models.card import Card
from src.models.card_id_mapping import CardIdMapping
from src.schemas import (
    ArchetypeDetailResponse,
    ArchetypeHistoryPoint,
    ArchetypeResponse,
    BestOf,
    CardUsageSummary,
    ConsensusDecklist,
    ConsensusDecklistCard,
    FormatForecastResponse,
    FormatNotes,
    JPSignals,
    KeyCardResponse,
    MatchupResponse,
    MatchupSpreadResponse,
    MetaComparisonResponse,
    MetaHistoryResponse,
    MetaSnapshotResponse,
    SampleDeckResponse,
    TrendInfo,
)
from src.schemas.freshness import CadenceProfile
from src.services.freshness import build_data_freshness
from src.services.meta_service import MetaService, TournamentType

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/meta",
    tags=["meta"],
    dependencies=[Depends(require_beta)],
)
limiter = Limiter(key_func=get_remote_address)


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


async def _load_display_overrides(
    db: AsyncSession,
) -> dict[str, str]:
    """Load archetype display_name overrides from the DB."""
    try:
        result = await db.execute(
            select(
                ArchetypeSprite.archetype_name,
                ArchetypeSprite.display_name,
            ).where(ArchetypeSprite.display_name.is_not(None))
        )
        return {
            row.archetype_name: row.display_name
            for row in result.all()
            if row.display_name
        }
    except SQLAlchemyError:
        logger.warning("Failed to load display overrides", exc_info=True)
        return {}


async def _load_archetype_sprites(
    db: AsyncSession,
) -> dict[str, list[str]]:
    """Load sprite URLs keyed by archetype_name."""
    try:
        result = await db.execute(
            select(
                ArchetypeSprite.archetype_name,
                ArchetypeSprite.sprite_urls,
            )
        )
        return {
            row.archetype_name: row.sprite_urls
            for row in result.all()
            if row.sprite_urls
        }
    except SQLAlchemyError:
        logger.warning("Failed to load archetype sprites", exc_info=True)
        return {}


async def _load_archetype_card_images(
    db: AsyncSession,
    archetype_names: list[str],
) -> dict[str, str | None]:
    """Derive a signature card image per archetype.

    Uses the first pokemon_name from archetype_sprites, looks up a
    matching card in the cards table, and returns its image_small.
    """
    if not archetype_names:
        return {}
    try:
        sprite_result = await db.execute(
            select(
                ArchetypeSprite.archetype_name,
                ArchetypeSprite.pokemon_names,
            ).where(ArchetypeSprite.archetype_name.in_(archetype_names))
        )
        name_to_pokemon: dict[str, str] = {}
        for row in sprite_result.all():
            if row.pokemon_names:
                name_to_pokemon[row.archetype_name] = row.pokemon_names[0]

        if not name_to_pokemon:
            return {}

        # Look up card images by pokemon name
        pokemon_names = list(set(name_to_pokemon.values()))
        card_result = await db.execute(
            select(Card.name, Card.image_small).where(
                Card.name.in_(pokemon_names),
                Card.image_small.is_not(None),
            )
        )
        pokemon_to_image: dict[str, str] = {}
        for row in card_result.all():
            if row.name not in pokemon_to_image and row.image_small:
                pokemon_to_image[row.name] = row.image_small

        return {
            arch_name: pokemon_to_image.get(poke_name)
            for arch_name, poke_name in name_to_pokemon.items()
        }
    except SQLAlchemyError:
        logger.warning("Failed to load archetype card images", exc_info=True)
        return {}


def _snapshot_to_response(
    snapshot: MetaSnapshot,
    include_format_notes: bool = True,
    display_overrides: dict[str, str] | None = None,
    card_info: dict[str, tuple[str | None, str | None]] | None = None,
    cadence_profile: CadenceProfile = "default_cadence",
    latest_tpci_event_end_date: date | None = None,
    archetype_sprites: dict[str, list[str]] | None = None,
    archetype_card_images: (dict[str, str | None] | None) = None,
) -> MetaSnapshotResponse:
    """Convert a MetaSnapshot model to response schema."""
    overrides = display_overrides or {}
    sprites = archetype_sprites or {}
    card_images = archetype_card_images or {}
    archetype_breakdown: list[ArchetypeResponse] = []
    for raw_name, share in (snapshot.archetype_shares or {}).items():
        name = str(raw_name)
        display = overrides.get(name, name)
        archetype_breakdown.append(
            ArchetypeResponse(
                name=display,
                share=share,
                sprite_urls=sprites.get(name),
                signature_card_image=card_images.get(name),
            )
        )

    card_info_map = card_info or {}
    card_usage = []
    if snapshot.card_usage:
        for card_id, usage_data in snapshot.card_usage.items():
            ci = card_info_map.get(card_id)
            card_usage.append(
                CardUsageSummary(
                    card_id=card_id,
                    card_name=ci[0] if ci else None,
                    image_small=ci[1] if ci else None,
                    inclusion_rate=usage_data.get("inclusion_rate", 0.0),
                    avg_copies=usage_data.get("avg_count", 0.0),
                )
            )

    format_notes = None
    if include_format_notes:
        format_notes = _get_format_notes(snapshot.best_of, snapshot.region)

    # Convert enhanced fields from raw DB dicts to typed schemas
    jp_signals = None
    if snapshot.jp_signals:
        jp_signals = JPSignals.model_validate(snapshot.jp_signals)

    trends = None
    if snapshot.trends:
        trends = {
            name: TrendInfo.model_validate(data)
            for name, data in snapshot.trends.items()
        }

    return MetaSnapshotResponse(
        snapshot_date=snapshot.snapshot_date,
        region=snapshot.region,
        format=snapshot.format,  # type: ignore[arg-type]
        best_of=snapshot.best_of,
        tournament_type=snapshot.tournament_type,  # type: ignore[arg-type]
        archetype_breakdown=archetype_breakdown,
        card_usage=card_usage,
        sample_size=snapshot.sample_size,
        tournaments_included=snapshot.tournaments_included,
        format_notes=format_notes,
        diversity_index=(
            float(snapshot.diversity_index)
            if snapshot.diversity_index is not None
            else None
        ),
        tier_assignments=snapshot.tier_assignments,
        jp_signals=jp_signals,
        trends=trends,
        era_label=snapshot.era_label,
        freshness=build_data_freshness(
            cadence_profile=cadence_profile,
            snapshot_date=snapshot.snapshot_date,
            sample_size=snapshot.sample_size,
            latest_tpci_event_end_date=latest_tpci_event_end_date,
            source_coverage=_source_coverage_for_meta(cadence_profile),
        ),
    )


def _source_coverage_for_meta(cadence_profile: CadenceProfile) -> list[str]:
    if cadence_profile == "tpci_event_cadence":
        return ["Limitless (major events)"]
    if cadence_profile == "jp_daily_cadence":
        return ["Limitless (JP)"]
    if cadence_profile == "grassroots_daily_cadence":
        return ["Limitless (community)"]
    return ["Limitless"]


def _meta_cadence_profile(
    region: str | None,
    best_of: int,
    tournament_type: TournamentType,
) -> CadenceProfile:
    if tournament_type == "official":
        return "tpci_event_cadence"
    if tournament_type == "grassroots":
        return "grassroots_daily_cadence"
    if (region == "JP") or best_of == 1:
        return "jp_daily_cadence"
    return "default_cadence"


async def _latest_tpci_event_end_date(
    db: AsyncSession,
    region: str | None,
    format: str,
) -> date | None:
    """Best-effort latest major event end date for TPCI cadence evaluation."""
    official_tiers = ["major", "worlds", "international", "regional", "special"]
    query = select(func.max(Tournament.date)).where(
        Tournament.tier.in_(official_tiers),
        Tournament.format == format,
    )
    if region is not None:
        query = query.where(Tournament.region == region)
    result = await db.execute(query)
    return result.scalar_one_or_none()


@router.get("/current")
@limiter.limit("60/minute")
async def get_current_meta(
    request: Request,
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
    era: Annotated[
        str | None,
        Query(description="Filter by era label (e.g., 'post-nihil-zero')"),
    ] = None,
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
) -> MetaSnapshotResponse:
    """Get the current (latest) meta snapshot.

    Returns the most recent meta snapshot matching the specified filters.
    Defaults to global region, standard format, and BO3.
    """
    query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
        MetaSnapshot.tournament_type == tournament_type,
    )

    if region is None:
        query = query.where(MetaSnapshot.region.is_(None))
    else:
        query = query.where(MetaSnapshot.region == region)

    if era:
        query = query.where(MetaSnapshot.era_label == era)

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

    overrides = await _load_display_overrides(db)
    cadence_profile = _meta_cadence_profile(region, best_of, tournament_type)
    latest_tpci_date = None
    if cadence_profile == "tpci_event_cadence":
        try:
            latest_tpci_date = await _latest_tpci_event_end_date(db, region, format)
        except SQLAlchemyError:
            logger.warning("Failed to load latest TPCI event date", exc_info=True)

    # Batch lookup card info for card_usage enrichment
    card_ids = list((snapshot.card_usage or {}).keys())
    ci = await _batch_lookup_cards(card_ids, db)

    # Load archetype sprite URLs and signature card images
    arch_sprites = await _load_archetype_sprites(db)
    arch_names = list((snapshot.archetype_shares or {}).keys())
    arch_card_images = await _load_archetype_card_images(db, arch_names)

    return _snapshot_to_response(
        snapshot,
        display_overrides=overrides,
        card_info=ci,
        cadence_profile=cadence_profile,
        latest_tpci_event_end_date=latest_tpci_date,
        archetype_sprites=arch_sprites,
        archetype_card_images=arch_card_images,
    )


@router.get("/history")
@limiter.limit("30/minute")
async def get_meta_history(
    request: Request,
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
        Query(
            ge=1,
            le=365,
            description="Number of days of history to return",
        ),
    ] = 90,
    era: Annotated[
        str | None,
        Query(description="Filter by era label (e.g., 'post-nihil-zero')"),
    ] = None,
    start_date_param: Annotated[
        date | None,
        Query(
            alias="start_date",
            description="Absolute start date (overrides days param)",
        ),
    ] = None,
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
) -> MetaHistoryResponse:
    """Get historical meta snapshots.

    Returns meta snapshots within the specified date range,
    ordered by snapshot date descending (newest first).
    """
    start_date = start_date_param or date.today() - timedelta(days=days)

    query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
        MetaSnapshot.snapshot_date >= start_date,
        MetaSnapshot.tournament_type == tournament_type,
    )

    if region is None:
        query = query.where(MetaSnapshot.region.is_(None))
    else:
        query = query.where(MetaSnapshot.region == region)

    if era:
        query = query.where(MetaSnapshot.era_label == era)

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

    overrides = await _load_display_overrides(db)
    cadence_profile = _meta_cadence_profile(region, best_of, tournament_type)
    latest_tpci_date = None
    if cadence_profile == "tpci_event_cadence":
        try:
            latest_tpci_date = await _latest_tpci_event_end_date(db, region, format)
        except SQLAlchemyError:
            logger.warning("Failed to load latest TPCI event date", exc_info=True)

    # Batch lookup card info for all snapshots' card_usage
    all_card_ids: set[str] = set()
    for s in snapshots:
        all_card_ids.update((s.card_usage or {}).keys())
    ci = await _batch_lookup_cards(list(all_card_ids), db)

    # Load archetype sprite URLs and signature card images
    arch_sprites = await _load_archetype_sprites(db)
    all_arch_names: set[str] = set()
    for s in snapshots:
        all_arch_names.update((s.archetype_shares or {}).keys())
    arch_card_images = await _load_archetype_card_images(db, list(all_arch_names))

    return MetaHistoryResponse(
        snapshots=[
            _snapshot_to_response(
                s,
                display_overrides=overrides,
                card_info=ci,
                cadence_profile=cadence_profile,
                latest_tpci_event_end_date=latest_tpci_date,
                archetype_sprites=arch_sprites,
                archetype_card_images=arch_card_images,
            )
            for s in snapshots
        ]
    )


@router.get("/archetypes")
@limiter.limit("60/minute")
async def list_archetypes(
    request: Request,
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
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
) -> list[ArchetypeResponse]:
    """List all archetypes from the current meta snapshot.

    Returns archetypes with their current meta share percentages,
    sorted by share descending (most popular first).
    """
    query = select(MetaSnapshot).where(
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
        MetaSnapshot.tournament_type == tournament_type,
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

    # Load archetype sprite URLs and signature card images
    arch_sprites = await _load_archetype_sprites(db)
    arch_names = list((snapshot.archetype_shares or {}).keys())
    arch_card_images = await _load_archetype_card_images(db, arch_names)

    overrides = await _load_display_overrides(db)
    archetypes = [
        ArchetypeResponse(
            name=overrides.get(str(name), str(name)),
            share=share,
            sprite_urls=arch_sprites.get(str(name)),
            signature_card_image=arch_card_images.get(str(name)),
        )
        for name, share in (snapshot.archetype_shares or {}).items()
    ]

    # Already sorted by share from compute_meta_snapshot, but ensure order
    archetypes.sort(key=lambda a: a.share, reverse=True)

    return archetypes


@router.get("/archetypes/{name}")
@limiter.limit("30/minute")
async def get_archetype_detail(
    request: Request,
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
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
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
        MetaSnapshot.tournament_type == tournament_type,
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
    current_share: float | None = None
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
            # Set current_share from first (most recent) snapshot only
            if current_share is None:
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

    if region is None:
        placement_query = placement_query.where(Tournament.region.is_(None))
    else:
        placement_query = placement_query.where(Tournament.region == region)

    placement_query = placement_query.order_by(
        TournamentPlacement.placement.asc()
    ).limit(100)

    try:
        placement_result = await db.execute(placement_query)
        placements = placement_result.scalars().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching archetype placements: "
            "name=%s, region=%s, format=%s, best_of=%s",
            name,
            region,
            format,
            best_of,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve archetype details. Please try again later.",
        ) from None

    # Compute key cards from placements with decklists
    key_cards = _compute_key_cards(placements)

    # Enrich key cards with names and images
    await _enrich_key_cards(key_cards, db)

    # Build sample decks from top placements
    sample_decks = await _build_sample_decks(placements[:10], db)

    # Compute consensus decklist
    consensus = await _compute_consensus_decklist(placements, db)

    return ArchetypeDetailResponse(
        name=name,
        current_share=current_share if current_share is not None else 0.0,
        history=history,
        key_cards=key_cards,
        sample_decks=sample_decks,
        consensus_decklist=consensus,
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


async def _compute_consensus_decklist(
    placements: Sequence[TournamentPlacement],
    db: AsyncSession,
) -> ConsensusDecklist | None:
    """Compute consensus decklist from tournament placements.

    For each card, computes inclusion rate, average copies,
    and copy count distribution. Groups by supertype.
    """
    placements_with_lists = [p for p in placements if p.decklist]
    if not placements_with_lists:
        return None

    total = len(placements_with_lists)
    card_appearances: dict[str, int] = defaultdict(int)
    card_total_count: dict[str, int] = defaultdict(int)
    # Track how many decks run N copies of each card
    card_count_dist: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    for placement in placements_with_lists:
        deck_counts: dict[str, int] = defaultdict(int)
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
            deck_counts[card_id] += quantity

        for card_id, count in deck_counts.items():
            card_appearances[card_id] += 1
            card_total_count[card_id] += count
            card_count_dist[card_id][count] += 1

    if not card_appearances:
        return None

    # Batch lookup card metadata (name, image, supertype)
    card_ids = list(card_appearances.keys())
    card_info = await _batch_lookup_cards(card_ids, db)

    # Get supertypes
    supertype_map = await _batch_lookup_supertypes(card_ids, db)

    # Build consensus cards
    pokemon: list[ConsensusDecklistCard] = []
    trainers: list[ConsensusDecklistCard] = []
    energy: list[ConsensusDecklistCard] = []

    for card_id in card_appearances:
        inclusion_rate = card_appearances[card_id] / total
        avg_copies = card_total_count[card_id] / card_appearances[card_id]
        dist = card_count_dist[card_id]
        count_distribution = {
            k: round(v / card_appearances[card_id], 2) for k, v in sorted(dist.items())
        }

        ci = card_info.get(card_id)
        supertype = supertype_map.get(card_id)

        card = ConsensusDecklistCard(
            card_id=card_id,
            card_name=ci[0] if ci else None,
            image_small=ci[1] if ci else None,
            supertype=supertype,
            inclusion_rate=round(inclusion_rate, 4),
            avg_copies=round(avg_copies, 2),
            count_distribution=count_distribution,
        )

        if supertype == "Pokémon":
            pokemon.append(card)
        elif supertype == "Energy":
            energy.append(card)
        else:
            trainers.append(card)

    # Sort each group by inclusion rate
    pokemon.sort(key=lambda c: c.inclusion_rate, reverse=True)
    trainers.sort(key=lambda c: c.inclusion_rate, reverse=True)
    energy.sort(key=lambda c: c.inclusion_rate, reverse=True)

    return ConsensusDecklist(
        pokemon=pokemon,
        trainers=trainers,
        energy=energy,
        decklists_analyzed=total,
    )


async def _batch_lookup_supertypes(
    card_ids: list[str],
    db: AsyncSession,
) -> dict[str, str]:
    """Batch lookup card supertypes from the cards table."""
    if not card_ids:
        return {}
    try:
        result = await db.execute(
            select(Card.id, Card.supertype).where(Card.id.in_(card_ids))
        )
        direct = {row.id: row.supertype for row in result.all()}

        # Fall back via card_id_mappings for JP cards
        missing = [cid for cid in card_ids if cid not in direct]
        if not missing:
            return direct

        mapping_q = select(
            CardIdMapping.jp_card_id,
            CardIdMapping.en_card_id,
        ).where(CardIdMapping.jp_card_id.in_(missing))
        mapping_result = await db.execute(mapping_q)
        jp_to_en = {r.jp_card_id: r.en_card_id for r in mapping_result.all()}

        if jp_to_en:
            en_q = select(Card.id, Card.supertype).where(
                Card.id.in_(list(jp_to_en.values()))
            )
            en_result = await db.execute(en_q)
            en_types = {r.id: r.supertype for r in en_result.all()}
            for jp_id, en_id in jp_to_en.items():
                if en_id in en_types:
                    direct[jp_id] = en_types[en_id]

        return direct
    except SQLAlchemyError:
        logger.warning("Failed to batch lookup supertypes", exc_info=True)
        return {}


async def _batch_lookup_cards(
    card_ids: list[str],
    db: AsyncSession,
) -> dict[str, tuple[str | None, str | None]]:
    """Batch lookup card names and images from the cards table.

    Returns dict of card_id -> (card_name, image_small).
    Falls back to card_id_mappings for JP card IDs not found directly.
    """
    if not card_ids:
        return {}
    try:
        # Step 1: Direct lookup in cards table
        query = select(Card.id, Card.name, Card.japanese_name, Card.image_small).where(
            Card.id.in_(card_ids)
        )
        result = await db.execute(query)
        card_info: dict[str, tuple[str | None, str | None]] = {
            row.id: (row.name or row.japanese_name, row.image_small)
            for row in result.all()
        }

        # Step 2: For missing IDs, check card_id_mappings
        missing_ids = [cid for cid in card_ids if cid not in card_info]
        if not missing_ids:
            return card_info

        mapping_query = select(
            CardIdMapping.jp_card_id,
            CardIdMapping.en_card_id,
            CardIdMapping.card_name_en,
        ).where(CardIdMapping.jp_card_id.in_(missing_ids))
        mapping_result = await db.execute(mapping_query)
        mappings = mapping_result.all()

        if not mappings:
            return card_info

        # Step 3: Look up EN cards and map back to JP IDs
        jp_to_en = {m.jp_card_id: m for m in mappings}
        en_ids = [m.en_card_id for m in mappings]

        en_query = select(
            Card.id,
            Card.name,
            Card.japanese_name,
            Card.image_small,
        ).where(Card.id.in_(en_ids))
        en_result = await db.execute(en_query)
        en_cards = {row.id: row for row in en_result.all()}

        for jp_id, mapping in jp_to_en.items():
            en_card = en_cards.get(mapping.en_card_id)
            if en_card:
                card_info[jp_id] = (
                    en_card.name or en_card.japanese_name,
                    en_card.image_small,
                )
            else:
                card_info[jp_id] = (mapping.card_name_en, None)

        return card_info
    except SQLAlchemyError:
        logger.warning("Failed to batch lookup cards", exc_info=True)
        return {}


async def _enrich_key_cards(
    key_cards: list[KeyCardResponse],
    db: AsyncSession,
) -> None:
    """Enrich key cards in-place with card names and images."""
    card_ids = [kc.card_id for kc in key_cards]
    card_info = await _batch_lookup_cards(card_ids, db)
    for kc in key_cards:
        info = card_info.get(kc.card_id)
        if info:
            kc.card_name = info[0]
            kc.image_small = info[1]


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
            logger.error(
                "Database error fetching tournaments for sample decks: "
                "tournament_ids=%s",
                tournament_ids,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to retrieve archetype details. Please try again later.",
            ) from None
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


def _compute_matchup_confidence(
    sample_size: int,
) -> Literal["high", "medium", "low"]:
    """Determine confidence level based on sample size."""
    if sample_size >= 50:
        return "high"
    elif sample_size >= 20:
        return "medium"
    return "low"


def _compute_matchups_from_placements(
    placements: Sequence[TournamentPlacement],
    archetype: str,
) -> tuple[list[MatchupResponse], float | None, int]:
    """Compute estimated matchup spread from tournament placements.

    Uses relative tournament placement as a proxy for matchup performance.
    When archetype A finishes ahead of archetype B in the same tournament,
    we count it as a favorable result for A.

    Note: This is an approximation. Actual matchup data would require
    head-to-head match results which we don't track.
    """
    # Group placements by tournament
    by_tournament: dict[str, list[TournamentPlacement]] = defaultdict(list)
    for p in placements:
        by_tournament[str(p.tournament_id)].append(p)

    # Track wins/losses against each opponent archetype
    matchup_wins: dict[str, float] = defaultdict(float)
    matchup_games: dict[str, int] = defaultdict(int)

    for tournament_placements in by_tournament.values():
        # Get archetype's best placement in this tournament
        archetype_placements = [
            p for p in tournament_placements if p.archetype == archetype
        ]
        if not archetype_placements:
            continue

        best_archetype_placement = min(p.placement for p in archetype_placements)

        # Compare against other archetypes
        other_archetypes: dict[str, int] = {}
        for p in tournament_placements:
            if p.archetype != archetype:
                if p.archetype not in other_archetypes:
                    other_archetypes[p.archetype] = p.placement
                else:
                    other_archetypes[p.archetype] = min(
                        other_archetypes[p.archetype], p.placement
                    )

        for opponent, opponent_placement in other_archetypes.items():
            matchup_games[opponent] += 1
            if best_archetype_placement < opponent_placement:
                matchup_wins[opponent] += 1
            elif best_archetype_placement == opponent_placement:
                # Tie counts as 0.5 win
                matchup_wins[opponent] += 0.5

    # Convert to matchup responses
    matchups: list[MatchupResponse] = []
    total_wins = 0.0
    total_games = 0

    sorted_opponents = sorted(
        matchup_games.keys(), key=lambda x: matchup_games[x], reverse=True
    )
    for opponent in sorted_opponents:
        games = matchup_games[opponent]
        wins = matchup_wins[opponent]
        win_rate = wins / games if games > 0 else 0.5

        matchups.append(
            MatchupResponse(
                opponent=opponent,
                win_rate=round(win_rate, 4),
                sample_size=games,
                confidence=_compute_matchup_confidence(games),
            )
        )
        total_wins += wins
        total_games += games

    # Sort by sample size (most data first)
    matchups.sort(key=lambda m: m.sample_size, reverse=True)

    overall_win_rate = round(total_wins / total_games, 4) if total_games > 0 else None

    return matchups, overall_win_rate, total_games


@router.get("/archetypes/{name}/matchups")
@limiter.limit("30/minute")
async def get_archetype_matchups(
    request: Request,
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
        Query(ge=1, le=365, description="Number of days of history to analyze"),
    ] = 90,
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
) -> MatchupSpreadResponse:
    """Get matchup spread for a specific archetype.

    Returns estimated win rates against other archetypes based on
    relative tournament performance. This is an approximation since
    we don't track individual head-to-head match results.

    Confidence levels:
    - high: 50+ comparisons
    - medium: 20-50 comparisons
    - low: <20 comparisons
    """
    start_date = date.today() - timedelta(days=days)

    # Get all placements from relevant tournaments
    placement_query = (
        select(TournamentPlacement)
        .join(Tournament)
        .where(
            Tournament.format == format,
            Tournament.best_of == best_of,
            Tournament.date >= start_date,
        )
    )

    if region is not None:
        placement_query = placement_query.where(Tournament.region == region)

    try:
        result = await db.execute(placement_query)
        all_placements = result.scalars().all()
    except SQLAlchemyError:
        logger.error(
            "Database error fetching placements for matchups: "
            "archetype=%s, region=%s, format=%s, best_of=%s",
            name,
            region,
            format,
            best_of,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve matchup data. Please try again later.",
        ) from None

    # Check if archetype exists in data
    archetype_exists = any(p.archetype == name for p in all_placements)
    if not archetype_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archetype '{name}' not found in tournament data",
        )

    matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
        all_placements, name
    )

    return MatchupSpreadResponse(
        archetype=name,
        matchups=matchups[:10],  # Top 10 matchups
        overall_win_rate=overall_win_rate,
        total_games=total_games,
    )


@router.get("/compare")
@limiter.limit("30/minute")
async def compare_meta(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    region_a: Annotated[
        str,
        Query(description="First region (e.g., JP)"),
    ] = "JP",
    region_b: Annotated[
        str | None,
        Query(description="Second region or null for Global"),
    ] = None,
    format: Annotated[
        Literal["standard", "expanded"],
        Query(description="Game format"),
    ] = "standard",
    lag_days: Annotated[
        int,
        Query(
            ge=0,
            le=90,
            description="Lag days for region_a snapshot",
        ),
    ] = 0,
    top_n: Annotated[
        int,
        Query(ge=1, le=30, description="Max archetypes"),
    ] = 15,
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
) -> MetaComparisonResponse:
    """Compare meta between two regions.

    Returns archetype-by-archetype comparison with divergence,
    tiers, sprites, and data confidence. Optionally includes
    lag-adjusted analysis.
    """
    svc = MetaService(db)
    try:
        return await svc.compute_meta_comparison(
            region_a=region_a,
            region_b=region_b,
            game_format=format,
            lag_days=lag_days,
            top_n=top_n,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None


@router.get("/forecast")
@limiter.limit("30/minute")
async def format_forecast(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[
        Literal["standard", "expanded"],
        Query(description="Game format"),
    ] = "standard",
    top_n: Annotated[
        int,
        Query(ge=1, le=10, description="Max archetypes"),
    ] = 5,
    tournament_type: Annotated[
        TournamentType,
        Query(description="Tournament type (all, official, grassroots)"),
    ] = "all",
) -> FormatForecastResponse:
    """Get format forecast based on JP meta divergence.

    Returns JP archetypes to watch, sorted by JP share,
    enriched with sprites, tiers, trends, and confidence.
    """
    svc = MetaService(db)
    try:
        return await svc.compute_format_forecast(
            game_format=format,
            top_n=top_n,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
