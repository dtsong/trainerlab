"""Deck service for database operations."""

from typing import Literal, cast
from uuid import UUID, uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.card import Card
from src.models.deck import Deck
from src.models.user import User
from src.schemas import (
    DeckCreate,
    DeckResponse,
    DeckSummaryResponse,
    DeckUpdate,
    PaginatedResponse,
)


class CardValidationError(Exception):
    """Raised when card IDs in a deck are invalid or don't exist."""

    pass


class DeckService:
    """Service for deck CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_deck(
        self,
        user: User,
        deck_data: DeckCreate,
    ) -> DeckResponse:
        """Create a new deck for a user.

        Args:
            user: The authenticated user creating the deck
            deck_data: Deck creation data

        Returns:
            The created deck response

        Raises:
            CardValidationError: If any card_id references don't exist
        """
        # Validate card references exist
        if deck_data.cards:
            card_ids = [card.card_id for card in deck_data.cards]
            await self._validate_card_ids(card_ids)

        # Create deck model
        deck = Deck(
            id=uuid4(),
            user_id=user.id,
            name=deck_data.name,
            description=deck_data.description,
            cards=[card.model_dump() for card in deck_data.cards],
            format=deck_data.format,
            is_public=deck_data.is_public,
        )

        self.session.add(deck)
        await self.session.commit()
        await self.session.refresh(deck)

        # Load user relationship for response
        await self.session.refresh(deck, ["user"])

        return self._to_response(deck)

    async def list_user_decks(
        self,
        user: User,
        *,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[DeckSummaryResponse]:
        """List decks for a specific user.

        Args:
            user: The authenticated user
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Paginated response with deck summaries
        """
        # Build query for user's decks
        query = (
            select(Deck).where(Deck.user_id == user.id).order_by(Deck.updated_at.desc())
        )

        # Get total count
        total = await self._get_total_count(query)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        decks = result.scalars().all()

        # Build response
        items = [self._to_summary_response(deck) for deck in decks]

        return PaginatedResponse[DeckSummaryResponse](
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_next=page * limit < total,
            has_prev=page > 1,
        )

    async def get_deck(
        self,
        deck_id: UUID,
        user: User | None = None,
    ) -> DeckResponse | None:
        """Get a single deck by ID.

        Args:
            deck_id: The deck ID
            user: The authenticated user (optional, for private deck access)

        Returns:
            DeckResponse if found and accessible, None otherwise
        """
        query = select(Deck).where(Deck.id == deck_id).options(selectinload(Deck.user))
        result = await self.session.execute(query)
        deck = result.scalar_one_or_none()

        if deck is None:
            return None

        # Check access: public decks are accessible to all,
        # private decks only to owner
        if not deck.is_public and (user is None or deck.user_id != user.id):
            return None

        return self._to_response(deck)

    async def update_deck(
        self,
        deck_id: UUID,
        user: User,
        deck_data: DeckUpdate,
    ) -> DeckResponse | None:
        """Update an existing deck.

        Args:
            deck_id: The deck ID
            user: The authenticated user (must be owner)
            deck_data: Partial update data

        Returns:
            Updated DeckResponse if found and owned, None otherwise

        Raises:
            CardValidationError: If any card_id references don't exist
        """
        query = select(Deck).where(Deck.id == deck_id).options(selectinload(Deck.user))
        result = await self.session.execute(query)
        deck = result.scalar_one_or_none()

        if deck is None or deck.user_id != user.id:
            return None

        # Validate card references if cards are being updated
        if deck_data.cards is not None:
            card_ids = [card.card_id for card in deck_data.cards]
            await self._validate_card_ids(card_ids)

        # Apply partial updates
        update_data = deck_data.model_dump(exclude_unset=True)
        if "cards" in update_data and deck_data.cards is not None:
            update_data["cards"] = [card.model_dump() for card in deck_data.cards]

        for field, value in update_data.items():
            setattr(deck, field, value)

        await self.session.commit()
        await self.session.refresh(deck, ["user"])

        return self._to_response(deck)

    async def _validate_card_ids(self, card_ids: list[str]) -> None:
        """Validate that all card IDs exist in the database.

        Args:
            card_ids: List of card IDs to validate

        Raises:
            CardValidationError: If any card IDs don't exist
        """
        if not card_ids:
            return

        # Get unique card IDs
        unique_ids = list(set(card_ids))

        # Query existing cards
        query = select(Card.id).where(Card.id.in_(unique_ids))
        result = await self.session.execute(query)
        existing_ids = {row[0] for row in result.all()}

        # Find missing IDs
        missing_ids = set(unique_ids) - existing_ids
        if missing_ids:
            raise CardValidationError(
                f"Card IDs not found: {', '.join(sorted(missing_ids))}"
            )

    async def _get_total_count(self, query: Select[tuple[Deck]]) -> int:
        """Get total count for a query (without pagination)."""
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar() or 0

    def _to_response(self, deck: Deck) -> DeckResponse:
        """Convert a Deck model to a DeckResponse."""
        return DeckResponse.model_validate(deck)

    def _to_summary_response(self, deck: Deck) -> DeckSummaryResponse:
        """Convert a Deck model to a DeckSummaryResponse."""
        # Calculate card count from cards JSONB
        card_count = sum(card.get("quantity", 0) for card in deck.cards)

        # Cast format string to literal (validated at insertion)
        format_literal = cast(Literal["standard", "expanded"], deck.format)

        return DeckSummaryResponse(
            id=deck.id,
            user_id=deck.user_id,
            name=deck.name,
            format=format_literal,
            archetype=deck.archetype,
            is_public=deck.is_public,
            card_count=card_count,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )
