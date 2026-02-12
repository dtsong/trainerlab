"""Ops alerts authentication dependency.

Used for low-scope operational endpoints (e.g. readiness checks) that should not
require full admin access but also should not be public.
"""

import hmac
import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


async def require_readiness_alert_token(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings | None, Depends(get_settings)] = None,
) -> None:
    if settings is None:
        settings = get_settings()

    expected = settings.readiness_alert_token
    if not expected:
        logger.error("readiness_alert_token not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ops alerts authentication not configured",
        )

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    if not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
