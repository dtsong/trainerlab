"""Card endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.schemas import CardSummaryResponse, PaginatedResponse
from src.services.card_service import CardService, SortField, SortOrder

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


@router.get("")
async def list_cards(
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
) -> PaginatedResponse[CardSummaryResponse]:
    """List all cards with pagination.

    Returns a paginated list of card summaries. Default page size is 20,
    maximum is 100. Results can be sorted by name, set, or date.

    Use the `q` parameter for case-insensitive partial matching on card names.
    """
    service = CardService(db)
    return await service.list_cards(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
    )
