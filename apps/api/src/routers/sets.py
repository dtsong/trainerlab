"""Set endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.schemas import CardSummaryResponse, PaginatedResponse, SetResponse
from src.services.set_service import SetService, SetSortField, SetSortOrder

router = APIRouter(prefix="/api/v1/sets", tags=["sets"])


@router.get("")
async def list_sets(
    db: Annotated[AsyncSession, Depends(get_db)],
    sort_by: Annotated[
        SetSortField, Query(description="Field to sort by")
    ] = SetSortField.RELEASE_DATE,
    sort_order: Annotated[
        SetSortOrder, Query(description="Sort order")
    ] = SetSortOrder.DESC,
    series: Annotated[str | None, Query(description="Filter by series name")] = None,
) -> list[SetResponse]:
    """List all card sets.

    Returns all sets sorted by release date (newest first by default).
    Use the `series` parameter to filter by series name (e.g., "Scarlet & Violet").
    """
    service = SetService(db)
    return await service.list_sets(
        sort_by=sort_by,
        sort_order=sort_order,
        series=series,
    )


@router.get("/{set_id}")
async def get_set(
    db: Annotated[AsyncSession, Depends(get_db)],
    set_id: str,
) -> SetResponse:
    """Get a single set by ID.

    Returns the full set details including release dates and legalities.
    """
    service = SetService(db)
    set_obj = await service.get_set(set_id)
    if set_obj is None:
        raise HTTPException(status_code=404, detail="Set not found")
    return set_obj


@router.get("/{set_id}/cards")
async def get_set_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    set_id: str,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Items per page (max 100)")
    ] = 20,
) -> PaginatedResponse[CardSummaryResponse]:
    """Get all cards in a set.

    Returns a paginated list of cards in the set, sorted by card number (local_id).
    """
    # First verify set exists
    service = SetService(db)
    set_obj = await service.get_set(set_id)
    if set_obj is None:
        raise HTTPException(status_code=404, detail="Set not found")

    return await service.get_set_cards(set_id, page=page, limit=limit)
