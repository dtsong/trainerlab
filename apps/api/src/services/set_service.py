"""Set query service for database operations."""

from enum import Enum

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.models.set import Set
from src.schemas import CardSummaryResponse, PaginatedResponse, SetResponse


class SetSortField(str, Enum):
    """Allowed sort fields for sets."""

    NAME = "name"
    RELEASE_DATE = "release_date"


class SetSortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class SetService:
    """Service for querying sets from the database."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_sets(
        self,
        *,
        sort_by: SetSortField = SetSortField.RELEASE_DATE,
        sort_order: SetSortOrder = SetSortOrder.DESC,
        series: str | None = None,
    ) -> list[SetResponse]:
        """List all sets with optional filtering.

        Args:
            sort_by: Field to sort by
            sort_order: Sort direction
            series: Filter by series name (optional)

        Returns:
            List of SetResponse objects
        """
        query = select(Set)

        # Apply series filter
        if series:
            query = query.where(Set.series == series)

        # Apply sorting
        query = self._apply_sorting(query, sort_by, sort_order)

        # Execute query
        result = await self.session.execute(query)
        sets = result.scalars().all()

        return [SetResponse.model_validate(s) for s in sets]

    async def get_set(self, set_id: str) -> SetResponse | None:
        """Get a single set by ID.

        Args:
            set_id: The set ID (e.g., "sv4")

        Returns:
            SetResponse if found, None otherwise
        """
        query = select(Set).where(Set.id == set_id)
        result = await self.session.execute(query)
        set_obj = result.scalar_one_or_none()
        if set_obj is None:
            return None
        return SetResponse.model_validate(set_obj)

    async def get_set_cards(
        self,
        set_id: str,
        *,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[CardSummaryResponse]:
        """Get all cards in a set.

        Args:
            set_id: The set ID
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Paginated response with card summaries sorted by local_id
        """
        # Build query for cards in this set
        query = select(Card).where(Card.set_id == set_id)

        # Sort by local_id (card number in set)
        query = query.order_by(Card.local_id)

        # Get total count
        total = await self._get_total_count(query)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        cards = result.scalars().all()

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
        query: Select[tuple[Set]],
        sort_by: SetSortField,
        sort_order: SetSortOrder,
    ) -> Select[tuple[Set]]:
        """Apply sorting to the query."""
        column = getattr(Set, sort_by.value)
        if sort_order == SetSortOrder.DESC:
            column = column.desc()
        return query.order_by(column)

    async def _get_total_count(self, query: Select[tuple[Card]]) -> int:
        """Get total count for a query (without pagination)."""
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar() or 0
