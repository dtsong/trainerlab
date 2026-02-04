"""User endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CurrentUser
from src.schemas.user import UserPreferencesUpdate, UserResponse
from src.services.user_service import DatabaseError, UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me")
@limiter.limit("30/minute")
async def get_current_user_info(
    request: Request,
    current_user: CurrentUser,
) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.get("/me/preferences")
@limiter.limit("30/minute")
async def get_user_preferences(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> dict:
    """Get the current user's preferences."""
    service = UserService(db)
    return await service.get_preferences(current_user)


@router.put("/me/preferences")
@limiter.limit("10/minute")
async def update_user_preferences(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    prefs: UserPreferencesUpdate,
) -> dict:
    """Update the current user's preferences.

    Only provided fields will be updated. Other preferences are preserved.
    """
    try:
        service = UserService(db)
        return await service.update_preferences(current_user, prefs)
    except DatabaseError as e:
        logger.error("Failed to update preferences: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again.",
        ) from e
