"""API Key authentication dependency for public API endpoints."""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.api_key import ApiKey, hash_api_key
from src.models.api_request import ApiRequest

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security.api_key")


def _log_api_key_event(
    event_type: str,
    request: Request | None = None,
    api_key_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a structured security event for API key access."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "api_key_id": api_key_id,
        "ip_address": request.client.host if request and request.client else None,
        "user_agent": (request.headers.get("user-agent") if request else None),
        "path": str(request.url.path) if request else None,
        "details": details or {},
    }
    security_logger.info(json.dumps(event))


async def get_api_key_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> ApiKey:
    """Authenticate request via API key.

    Validates the X-API-Key header and returns the associated ApiKey.
    Implements lazy monthly reset of request counter.

    Args:
        request: FastAPI request object
        db: Database session
        x_api_key: X-API-Key header value

    Returns:
        ApiKey model for the authenticated key

    Raises:
        HTTPException: 401 if key missing or invalid
        HTTPException: 429 if monthly rate limit exceeded
    """
    if not x_api_key:
        _log_api_key_event(
            "api_key_missing",
            request=request,
            details={"reason": "No X-API-Key header provided"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )

    key_hash = hash_api_key(x_api_key)
    query = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()

    if api_key is None:
        _log_api_key_event(
            "api_key_invalid",
            request=request,
            details={"reason": "Invalid or revoked API key"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Lazy monthly reset using updated_at from TimestampMixin
    now = datetime.now(UTC)
    if api_key.updated_at.month != now.month or api_key.updated_at.year != now.year:
        api_key.requests_this_month = 0
        logger.info("Reset monthly counter for API key %s", api_key.id)

    # Check rate limit
    if api_key.requests_this_month >= api_key.monthly_limit:
        _log_api_key_event(
            "api_key_rate_limited",
            request=request,
            api_key_id=str(api_key.id),
            details={
                "monthly_limit": api_key.monthly_limit,
                "requests_this_month": api_key.requests_this_month,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly rate limit exceeded",
            headers={"X-RateLimit-Limit": str(api_key.monthly_limit)},
        )

    # Increment request counter
    api_key.requests_this_month += 1
    await db.commit()

    _log_api_key_event(
        "api_key_authenticated",
        request=request,
        api_key_id=str(api_key.id),
        details={"requests_this_month": api_key.requests_this_month},
    )

    return api_key


async def record_api_request(
    api_key: ApiKey,
    request: Request,
    db: AsyncSession,
    status_code: int,
    response_time_ms: int | None = None,
) -> None:
    """Record an API request for analytics.

    Args:
        api_key: The authenticated API key
        request: FastAPI request object
        db: Database session
        status_code: HTTP response status code
        response_time_ms: Response time in milliseconds (optional)
    """
    api_request = ApiRequest(
        id=uuid4(),
        api_key_id=api_key.id,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=status_code,
        response_time_ms=response_time_ms,
    )
    db.add(api_request)
    await db.commit()


ApiKeyAuth = Annotated[ApiKey, Depends(get_api_key_user)]
