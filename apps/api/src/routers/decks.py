"""Deck endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CurrentUser, OptionalUser
from src.schemas import (
    DeckCreate,
    DeckResponse,
    DeckSummaryResponse,
    PaginatedResponse,
)
from src.services.deck_service import DeckService

router = APIRouter(prefix="/api/v1/decks", tags=["decks"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_deck(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    deck_data: DeckCreate,
) -> DeckResponse:
    """Create a new deck.

    Requires authentication. Creates a deck for the authenticated user.
    Card IDs are validated to ensure they exist in the database.
    """
    service = DeckService(db)
    try:
        return await service.create_deck(current_user, deck_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("")
async def list_decks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Items per page (max 100)")
    ] = 20,
) -> PaginatedResponse[DeckSummaryResponse]:
    """List the authenticated user's decks.

    Requires authentication. Returns only decks belonging to the
    authenticated user, sorted by most recently updated.
    """
    service = DeckService(db)
    return await service.list_user_decks(current_user, page=page, limit=limit)


@router.get("/{deck_id}")
async def get_deck(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: OptionalUser,
    deck_id: UUID,
) -> DeckResponse:
    """Get a single deck by ID.

    Public decks are accessible to everyone. Private decks require
    authentication and are only accessible to their owner.
    """
    service = DeckService(db)
    deck = await service.get_deck(deck_id, current_user)
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return deck
