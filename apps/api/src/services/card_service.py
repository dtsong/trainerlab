"""Card query service for database operations."""

from enum import Enum

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.schemas import CardSummaryResponse, PaginatedResponse


class SortField(str, Enum):
    """Allowed sort fields for cards."""

    NAME = "name"
    SET = "set_id"
    DATE = "created_at"


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class CardService:
    """Service for querying cards from the database."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_cards(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        sort_by: SortField = SortField.NAME,
        sort_order: SortOrder = SortOrder.ASC,
        q: str | None = None,
        supertype: list[str] | None = None,
        types: list[str] | None = None,
    ) -> PaginatedResponse[CardSummaryResponse]:
        """List cards with pagination and sorting.

        Args:
            page: Page number (1-indexed)
            limit: Items per page (max 100)
            sort_by: Field to sort by
            sort_order: Sort direction
            q: Optional text search query (searches name field)
            supertype: Filter by supertype(s) (Pokemon, Trainer, Energy)
            types: Filter by Pokemon type(s) (Fire, Water, Grass, etc.)

        Returns:
            Paginated response with card summaries
        """
        # Build base query
        query = select(Card)

        # Apply text search filter
        if q:
            query = query.where(Card.name.ilike(f"%{q}%"))

        # Apply supertype filter
        if supertype:
            query = query.where(Card.supertype.in_(supertype))

        # Apply types filter (array overlap)
        if types:
            query = query.where(Card.types.overlap(types))

        # Apply sorting
        query = self._apply_sorting(query, sort_by, sort_order)

        # Get total count
        total = await self._get_total_count(query)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        cards = result.scalars().all()

        # Build response
        items = [CardSummaryResponse.model_validate(card) for card in cards]

        return PaginatedResponse[CardSummaryResponse](
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_next=page * limit < total,
            has_prev=page > 1,
        )

    def _apply_sorting(
        self,
        query: Select[tuple[Card]],
        sort_by: SortField,
        sort_order: SortOrder,
    ) -> Select[tuple[Card]]:
        """Apply sorting to the query."""
        column = getattr(Card, sort_by.value)
        if sort_order == SortOrder.DESC:
            column = column.desc()
        return query.order_by(column)

    async def _get_total_count(self, query: Select[tuple[Card]]) -> int:
        """Get total count for a query (without pagination)."""
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar() or 0
