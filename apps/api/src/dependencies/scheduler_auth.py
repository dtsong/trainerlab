"""Pipeline authentication dependency.

Verifies OIDC tokens sent by Cloud Scheduler or Operations SA to protect
pipeline endpoints. Tokens must have:
- Audience: Cloud Run service URL
- Email: Either scheduler_service_account or operations_service_account
"""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import requests
from google.oauth2 import id_token

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SchedulerAuthError(Exception):
    """Exception raised for scheduler authentication failures."""

    pass


def _verify_oidc_token(
    token: str,
    expected_audience: str,
    allowed_emails: list[str] | None = None,
) -> dict:
    """Verify an OIDC token from Cloud Scheduler or Operations SA.

    Args:
        token: The Bearer token (without "Bearer " prefix).
        expected_audience: Expected audience claim (Cloud Run URL).
        allowed_emails: List of allowed email claims (scheduler + operations SAs).

    Returns:
        Decoded token claims.

    Raises:
        SchedulerAuthError: If verification fails.
    """
    try:
        claims = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=expected_audience,
        )

        # Verify email if required
        if allowed_emails:
            token_email = claims.get("email", "")
            if token_email not in allowed_emails:
                raise SchedulerAuthError(
                    f"Token email not allowed: got {token_email}, "
                    f"expected one of {allowed_emails}"
                )

        return claims

    except (ValueError, google_auth_exceptions.GoogleAuthError) as e:
        raise SchedulerAuthError(f"Token verification failed: {e}") from e


async def verify_scheduler_auth(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings | None, Depends(get_settings)] = None,
) -> dict | None:
    """FastAPI dependency to verify pipeline authentication.

    This dependency protects pipeline endpoints by verifying OIDC tokens
    from authorized service accounts (scheduler or operations).

    In development (scheduler_auth_bypass=True), this returns None
    and allows requests through.

    Args:
        authorization: Authorization header value.
        settings: Application settings.

    Returns:
        Token claims if verified, None if bypassed.

    Raises:
        HTTPException: If authentication fails.
    """
    if settings is None:
        settings = get_settings()

    # Allow bypass in development
    if settings.scheduler_auth_bypass:
        logger.debug("Scheduler auth bypassed (development mode)")
        return None

    # Require auth in production
    if not authorization:
        logger.warning("Missing Authorization header for pipeline endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Check configuration
    if not settings.cloud_run_url:
        logger.error("cloud_run_url not configured for scheduler auth")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scheduler authentication not configured",
        )

    try:
        # Build list of allowed service accounts
        allowed_emails = []
        if settings.scheduler_service_account:
            allowed_emails.append(settings.scheduler_service_account)
        if settings.operations_service_account:
            allowed_emails.append(settings.operations_service_account)
        if settings.api_service_account:
            allowed_emails.append(settings.api_service_account)

        claims = _verify_oidc_token(
            token=token,
            expected_audience=settings.cloud_run_url,
            allowed_emails=allowed_emails if allowed_emails else None,
        )

        token_email = claims.get("email", "unknown")
        logger.info("Pipeline auth successful: email=%s", token_email)

        # Log whether this is scheduler or manual operation
        if token_email == settings.operations_service_account:
            logger.info("Manual operation via operations service account")
        elif token_email == settings.scheduler_service_account:
            logger.info("Automated operation via scheduler service account")

        return claims

    except SchedulerAuthError as e:
        logger.warning("Pipeline auth failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
