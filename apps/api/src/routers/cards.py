"""Card endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.schemas import (
    CardResponse,
    CardSummaryResponse,
    CardUsageResponse,
    PaginatedResponse,
)
from src.services.card_service import CardService, SortField, SortOrder
from src.services.usage_service import UsageService

router = APIRouter(
    prefix="/api/v1/cards",
    tags=["cards"],
    dependencies=[Depends(require_beta)],
)
limiter = Limiter(key_func=get_remote_address)


@router.get("")
@limiter.limit("100/minute")
async def list_cards(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Items per page (max 100)")
    ] = 20,
    sort_by: Annotated[
        SortField, Query(description="Field to sort by")
    ] = SortField.NAME,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.ASC,
    q: Annotated[
        str | None, Query(description="Search query (searches card name)")
    ] = None,
    supertype: Annotated[
        list[str] | None,
        Query(description="Filter by supertype (Pokemon, Trainer, Energy)"),
    ] = None,
    types: Annotated[
        list[str] | None,
        Query(description="Filter by Pokemon type (Fire, Water, Grass, etc.)"),
    ] = None,
    set_id: Annotated[
        str | None,
        Query(description="Filter by set ID (e.g., sv4, swsh1)"),
    ] = None,
    standard: Annotated[
        bool | None,
        Query(description="Filter by standard format legality"),
    ] = None,
    expanded: Annotated[
        bool | None,
        Query(description="Filter by expanded format legality"),
    ] = None,
) -> PaginatedResponse[CardSummaryResponse]:
    """List all cards with pagination.

    Returns a paginated list of card summaries. Default page size is 20,
    maximum is 100. Results can be sorted by name, set, or date.

    Use the `q` parameter for case-insensitive partial matching on card names.
    Use the `supertype` parameter to filter by card type. Multiple values can
    be provided: ?supertype=Pokemon&supertype=Trainer
    Use the `types` parameter to filter by Pokemon type. Returns cards that
    have any of the specified types: ?types=Fire&types=Water
    Use the `set_id` parameter to filter by exact set ID.
    Use `standard=true` or `expanded=true` to filter by format legality.
    """
    service = CardService(db)
    return await service.list_cards(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
        supertype=supertype,
        types=types,
        set_id=set_id,
        standard=standard,
        expanded=expanded,
    )


@router.get("/search")
@limiter.limit("60/minute")
async def search_cards(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[
        str,
        Query(min_length=2, description="Search query (min 2 characters)"),
    ],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Items per page (max 100)")
    ] = 20,
    supertype: Annotated[
        list[str] | None,
        Query(description="Filter by supertype (Pokemon, Trainer, Energy)"),
    ] = None,
    types: Annotated[
        list[str] | None,
        Query(description="Filter by Pokemon type (Fire, Water, Grass, etc.)"),
    ] = None,
    set_id: Annotated[
        str | None,
        Query(description="Filter by set ID (e.g., sv4, swsh1)"),
    ] = None,
    standard: Annotated[
        bool | None,
        Query(description="Filter by standard format legality"),
    ] = None,
    expanded: Annotated[
        bool | None,
        Query(description="Filter by expanded format legality"),
    ] = None,
    search_text: Annotated[
        bool,
        Query(description="Also search abilities, attacks, and rules text"),
    ] = False,
) -> PaginatedResponse[CardSummaryResponse]:
    """Search cards with fuzzy matching and relevance ranking.

    This endpoint provides advanced search capabilities:

    - **Fuzzy name matching**: Handles typos (e.g., "pikchu" finds "Pikachu")
    - **Relevance ranking**: Results sorted by match quality
    - **Text search**: Optionally search ability/attack names and effects

    Use `search_text=true` to also search within:
    - Ability names and effects
    - Attack names, effects, and descriptions
    - Rule box text

    Results are ranked by relevance:
    1. Exact name matches
    2. Names starting with the query
    3. High similarity matches
    4. Partial name matches
    5. Text field matches
    """
    service = CardService(db)
    return await service.search_cards(
        q=q,
        page=page,
        limit=limit,
        supertype=supertype,
        types=types,
        set_id=set_id,
        standard=standard,
        expanded=expanded,
        search_text=search_text,
    )


@router.get("/batch")
@limiter.limit("60/minute")
async def get_cards_batch(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    ids: Annotated[
        str,
        Query(description="Comma-separated card IDs (max 50)"),
    ],
) -> list[CardSummaryResponse]:
    """Get multiple cards by IDs in a single request.

    Accepts a comma-separated list of card IDs (max 50).
    Returns matching card summaries. Unknown IDs are silently skipped.
    """
    card_ids = [cid.strip() for cid in ids.split(",") if cid.strip()][:50]
    if not card_ids:
        return []
    service = CardService(db)
    return await service.get_cards_batch(card_ids)


@router.get("/{card_id}")
@limiter.limit("100/minute")
async def get_card(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    card_id: str,
) -> CardResponse:
    """Get a single card by ID.

    Returns the full card details including all stats, attacks, abilities, etc.
    """
    service = CardService(db)
    card = await service.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.get("/{card_id}/usage")
@limiter.limit("60/minute")
async def get_card_usage(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    card_id: str,
    format: Annotated[
        str, Query(description="Format to get usage for (standard/expanded)")
    ] = "standard",
    days: Annotated[
        int, Query(ge=1, le=90, description="Days of trend data (max 90)")
    ] = 30,
) -> CardUsageResponse:
    """Get usage statistics for a card.

    Returns inclusion rate, average copies, and trend data from meta snapshots.
    """
    # First verify card exists
    card_service = CardService(db)
    card = await card_service.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    usage_service = UsageService(db)
    usage = await usage_service.get_card_usage(card_id, format=format, days=days)

    # If no meta data exists, return zero usage
    if usage is None:
        return CardUsageResponse(
            card_id=card_id,
            format=format,
            inclusion_rate=0.0,
            avg_copies=None,
            trend=[],
            sample_size=0,
        )

    return usage
