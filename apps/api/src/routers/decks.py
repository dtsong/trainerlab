"""Deck endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CurrentUser, OptionalUser
from src.schemas import (
    DeckCreate,
    DeckResponse,
    DeckStatsResponse,
    DeckSummaryResponse,
    DeckUpdate,
    PaginatedResponse,
)
from src.services.deck_service import CardValidationError, DeckService

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
    except CardValidationError as e:
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


@router.get("/{deck_id}/stats")
async def get_deck_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: OptionalUser,
    deck_id: UUID,
) -> DeckStatsResponse:
    """Get statistics for a deck.

    Returns type breakdown, average HP, energy curve, and attack
    cost distribution. Public decks are accessible to everyone.
    """
    service = DeckService(db)
    stats = await service.get_deck_stats(deck_id, current_user)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return stats


@router.put("/{deck_id}")
async def update_deck(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    deck_id: UUID,
    deck_data: DeckUpdate,
) -> DeckResponse:
    """Update an existing deck.

    Requires authentication. Only the deck owner can update it.
    All fields are optional for partial updates.
    """
    service = DeckService(db)
    try:
        deck = await service.update_deck(deck_id, current_user, deck_data)
    except CardValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    deck_id: UUID,
) -> Response:
    """Delete a deck.

    Requires authentication. Only the deck owner can delete it.
    """
    service = DeckService(db)
    deleted = await service.delete_deck(deck_id, current_user)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
