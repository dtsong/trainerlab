"""Card query service for database operations."""

from enum import Enum

from sqlalchemy import Select, case, cast, func, or_, select
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.schemas import CardResponse, CardSummaryResponse, PaginatedResponse


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
        set_id: str | None = None,
        standard: bool | None = None,
        expanded: bool | None = None,
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
            set_id: Filter by exact set ID
            standard: Filter by standard format legality
            expanded: Filter by expanded format legality

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

        # Apply set_id filter
        if set_id:
            query = query.where(Card.set_id == set_id)

        # Apply legality filters (JSON path)
        if standard is True:
            query = query.where(Card.legalities["standard"].astext == "true")
        if expanded is True:
            query = query.where(Card.legalities["expanded"].astext == "true")

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

    async def get_card(self, card_id: str) -> CardResponse | None:
        """Get a single card by ID.

        Args:
            card_id: The card ID (e.g., "sv4-6")

        Returns:
            CardResponse if found, None otherwise
        """
        query = select(Card).where(Card.id == card_id)
        result = await self.session.execute(query)
        card = result.scalar_one_or_none()
        if card is None:
            return None
        return CardResponse.model_validate(card)

    async def search_cards(
        self,
        *,
        q: str,
        page: int = 1,
        limit: int = 20,
        supertype: list[str] | None = None,
        types: list[str] | None = None,
        set_id: str | None = None,
        standard: bool | None = None,
        expanded: bool | None = None,
        search_text: bool = False,
    ) -> PaginatedResponse[CardSummaryResponse]:
        """Search cards with fuzzy name matching and optional text search.

        Uses PostgreSQL trigram similarity for typo-tolerant name search
        (e.g., "pikchu" finds "Pikachu"). When search_text=True, also searches
        ability names, attack names/effects, and rules text.

        Args:
            q: Search query (required, min 2 chars for fuzzy matching)
            page: Page number (1-indexed)
            limit: Items per page (max 100)
            supertype: Filter by supertype(s)
            types: Filter by Pokemon type(s)
            set_id: Filter by exact set ID
            standard: Filter by standard format legality
            expanded: Filter by expanded format legality
            search_text: If True, also search abilities, attacks, and rules

        Returns:
            Paginated response with card summaries, ranked by relevance
        """
        # Build search conditions
        search_conditions = self._build_search_conditions(q, search_text)

        # Build base query with relevance scoring
        relevance_score = self._build_relevance_score(q)
        query = select(Card, relevance_score.label("relevance")).where(
            or_(*search_conditions)
        )

        # Apply filters
        query = self._apply_filters(query, supertype, types, set_id, standard, expanded)

        # Get total count (without relevance column)
        count_subquery = select(Card.id).where(or_(*search_conditions))
        count_subquery = self._apply_filters(
            count_subquery, supertype, types, set_id, standard, expanded
        )
        count_query = select(func.count()).select_from(count_subquery.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Order by relevance (highest first), then name
        query = query.order_by(relevance_score.desc(), Card.name)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        cards = [row[0] for row in rows]  # Extract Card from (Card, relevance) tuples

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

    def _build_search_conditions(self, query: str, search_text: bool) -> list:
        """Build search conditions for fuzzy and text matching."""
        conditions = []

        # Trigram similarity on name (handles typos like "pikchu" -> "Pikachu")
        # Uses pg_trgm's similarity function with 0.3 threshold
        conditions.append(func.similarity(Card.name, query) > 0.3)

        # Also do case-insensitive contains for exact substring matches
        conditions.append(Card.name.ilike(f"%{query}%"))

        # Search Japanese name if provided
        conditions.append(
            (Card.japanese_name.isnot(None)) & (Card.japanese_name.ilike(f"%{query}%"))
        )

        if search_text:
            # Search in abilities JSONB (ability names and effects)
            # abilities is an array of objects like [{"name": "...", "effect": "..."}]
            conditions.append(cast(Card.abilities, TEXT).ilike(f"%{query}%"))

            # Search in attacks JSONB (attack names and effects)
            # attacks is an array of objects like [{"name": "...", "effect": "..."}]
            conditions.append(cast(Card.attacks, TEXT).ilike(f"%{query}%"))

            # Search in rules text array
            conditions.append(func.array_to_string(Card.rules, " ").ilike(f"%{query}%"))

        return conditions

    def _build_relevance_score(self, query: str):
        """Build relevance score for ranking search results.

        Scoring:
        - Exact name match: 100
        - Name starts with query: 80
        - High trigram similarity (>0.6): 60
        - Medium trigram similarity (>0.4): 40
        - Name contains query: 30
        - Text fields contain query: 10
        """
        name_similarity = func.similarity(Card.name, query)

        return case(
            # Exact match (case-insensitive)
            (func.lower(Card.name) == func.lower(query), 100),
            # Name starts with query
            (Card.name.ilike(f"{query}%"), 80),
            # High trigram similarity
            (name_similarity > 0.6, 60),
            # Medium trigram similarity
            (name_similarity > 0.4, 40),
            # Name contains query
            (Card.name.ilike(f"%{query}%"), 30),
            # Default: low relevance (matched on text fields)
            else_=10,
        )

    def _apply_filters(
        self,
        query: Select,
        supertype: list[str] | None,
        types: list[str] | None,
        set_id: str | None,
        standard: bool | None,
        expanded: bool | None,
    ) -> Select:
        """Apply filters to a query."""
        if supertype:
            query = query.where(Card.supertype.in_(supertype))
        if types:
            query = query.where(Card.types.overlap(types))
        if set_id:
            query = query.where(Card.set_id == set_id)
        if standard is True:
            query = query.where(Card.legalities["standard"].astext == "true")
        if expanded is True:
            query = query.where(Card.legalities["expanded"].astext == "true")
        return query
