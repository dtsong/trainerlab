"""Authentication dependencies for FastAPI endpoints.

This module provides dependency injection functions for authentication.
Currently uses a placeholder implementation that will be replaced with
Firebase Auth verification in a future issue.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.user import User


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Get the current authenticated user.

    Currently expects a user ID in the Authorization header for development.
    Will be replaced with Firebase token verification.

    Args:
        db: Database session
        authorization: Authorization header (format: "Bearer <user_id>")

    Returns:
        User model for the authenticated user

    Raises:
        HTTPException: If authorization header is missing or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse "Bearer <user_id>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(parts[1])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Look up user in database
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """Get the current user if authenticated, None otherwise.

    Used for endpoints that have different behavior for authenticated
    vs unauthenticated users (e.g., viewing public decks).

    If no authorization header is provided, returns None (anonymous access).
    If an authorization header IS provided, it must be valid - invalid tokens
    will raise 401 rather than silently falling back to anonymous access.

    Args:
        db: Database session
        authorization: Authorization header (optional)

    Returns:
        User model if authenticated, None if no auth header provided

    Raises:
        HTTPException: If authorization header is provided but invalid
    """
    if not authorization:
        return None

    # If auth is provided, it must be valid - don't silently fall back to anonymous
    return await get_current_user(db, authorization)


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
