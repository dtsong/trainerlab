"""Authentication dependencies for FastAPI endpoints.

This module provides dependency injection functions for Firebase Auth.
"""

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.firebase import TokenVerificationError, verify_token
from src.db.database import get_db
from src.models.user import User

logger = logging.getLogger(__name__)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Get the current authenticated user from Firebase token.

    Verifies the Firebase ID token and returns the corresponding user.
    If the user doesn't exist in the database, creates them automatically.

    Args:
        db: Database session
        authorization: Authorization header (format: "Bearer <firebase_id_token>")

    Returns:
        User model for the authenticated user

    Raises:
        HTTPException: 401 Unauthorized if:
            - Authorization header is missing
            - Authorization header format is invalid (not "Bearer <token>")
            - Firebase token is invalid, expired, or revoked
            - Token missing email claim (required for new user creation)
        HTTPException: 503 Service Unavailable if:
            - Token verification fails due to infrastructure issues
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Verify Firebase token
    try:
        decoded = await verify_token(token)
    except TokenVerificationError as e:
        logger.error("Token verification infrastructure error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        ) from e

    if decoded is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user by Firebase UID (uid is guaranteed present in DecodedToken)
    query = select(User).where(User.firebase_uid == decoded.uid)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Auto-create user if they don't exist (first login)
    # Note: Requires email - phone-only or anonymous Firebase users are rejected
    if user is None:
        if not decoded.email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email required for account creation",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = User(
            id=uuid4(),
            firebase_uid=decoded.uid,
            email=decoded.email,
            display_name=decoded.name,
            avatar_url=decoded.picture,
        )
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("Created new user from Firebase: %s", decoded.uid)
        except IntegrityError as e:
            # Race condition: user was created by concurrent request
            await db.rollback()
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                logger.error("User creation failed unexpectedly: %s", decoded.uid)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Account creation failed, please try again",
                ) from e
            logger.info("User already created by concurrent request: %s", decoded.uid)

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
