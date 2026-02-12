"""Authentication dependencies for FastAPI endpoints.

This module provides dependency injection functions for JWT-based auth
using NextAuth.js HS256-signed tokens.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.jwt import TokenVerificationError, verify_token
from src.db.database import get_db
from src.models.access_grant import AccessGrant
from src.models.user import User

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security.auth")


def _log_security_event(
    event_type: str,
    request: Request | None = None,
    user_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a structured security event."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": request.client.host if request and request.client else None,
        "user_agent": (request.headers.get("user-agent") if request else None),
        "path": str(request.url.path) if request else None,
        "details": details or {},
    }
    security_logger.warning(json.dumps(event))


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Get the current authenticated user from JWT token.

    Verifies the NextAuth.js JWT and returns the corresponding user.
    If the user doesn't exist in the database, creates them automatically.

    Args:
        db: Database session
        authorization: Authorization header (format: "Bearer <jwt>")

    Returns:
        User model for the authenticated user

    Raises:
        HTTPException: 401 Unauthorized if:
            - Authorization header is missing
            - Authorization header format is invalid (not "Bearer <token>")
            - JWT is invalid or expired
            - Token missing email claim (required for new user creation)
        HTTPException: 503 Service Unavailable if:
            - Token verification fails due to infrastructure issues
    """
    if not authorization:
        _log_security_event(
            "auth_missing_header",
            request=request,
            details={"reason": "No Authorization header provided"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        _log_security_event(
            "auth_invalid_format",
            request=request,
            details={"reason": "Invalid Authorization header format"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Verify JWT
    try:
        decoded = verify_token(token)
    except TokenVerificationError as e:
        logger.error("Token verification infrastructure error: %s", e)
        _log_security_event(
            "auth_verification_error",
            request=request,
            details={"reason": "Token verification infrastructure error"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        ) from e

    if decoded is None:
        _log_security_event(
            "auth_invalid_token",
            request=request,
            details={"reason": "Invalid or expired token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user by auth provider ID (sub claim)
    query = select(User).where(User.auth_provider_id == decoded.sub)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Fallback lookup by email to avoid lockout when provider subject changes
    if user is None and decoded.email:
        email_query = select(User).where(
            func.lower(User.email) == decoded.email.lower()
        )
        email_result = await db.execute(email_query)
        user = email_result.scalar_one_or_none()

    # Auto-create user if they don't exist (first login)
    if user is None:
        if not decoded.email:
            _log_security_event(
                "auth_missing_email",
                request=request,
                details={
                    "reason": "Email required for account creation",
                    "sub": decoded.sub,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email required for account creation",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = User(
            id=uuid4(),
            auth_provider_id=decoded.sub,
            email=decoded.email,
            display_name=decoded.name,
            avatar_url=decoded.picture,
            is_beta_tester=False,
        )
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("Created new user: %s", decoded.sub)
        except IntegrityError as e:
            # Race condition: user was created by concurrent request
            await db.rollback()
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            if user is None and decoded.email:
                email_query = select(User).where(
                    func.lower(User.email) == decoded.email.lower()
                )
                email_result = await db.execute(email_query)
                user = email_result.scalar_one_or_none()
            if not user:
                logger.error("User creation failed unexpectedly: %s", decoded.sub)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Account creation failed, please try again",
                ) from e
            logger.info("User already created by concurrent request: %s", decoded.sub)

    # Apply email-based access grants (pre-login invites)
    if decoded.email:
        grant_result = await db.execute(
            select(AccessGrant).where(
                func.lower(AccessGrant.email) == decoded.email.lower()
            )
        )
        grant = grant_result.scalar_one_or_none()

        if grant:
            changed = False
            if grant.is_beta_tester and not user.is_beta_tester:
                user.is_beta_tester = True
                changed = True
            if grant.is_subscriber and not user.is_subscriber:
                user.is_subscriber = True
                changed = True

            if changed:
                await db.commit()
                await db.refresh(user)

    return user


async def get_current_user_optional(
    request: Request,
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
        request: FastAPI request object
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
    return await get_current_user(request, db, authorization)


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
