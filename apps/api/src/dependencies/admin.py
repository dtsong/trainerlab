"""Admin authorization dependency."""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from src.config import get_settings
from src.dependencies.auth import CurrentUser
from src.models.user import User

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security.admin")


def _log_admin_security_event(
    event_type: str,
    request: Request | None = None,
    user_email: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a structured security event for admin access."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "user_email": user_email,
        "ip_address": request.client.host if request and request.client else None,
        "user_agent": (request.headers.get("user-agent") if request else None),
        "path": str(request.url.path) if request else None,
        "details": details or {},
    }
    security_logger.warning(json.dumps(event))


async def require_admin(request: Request, current_user: CurrentUser) -> User:
    """Verify the current user is an admin.

    Checks user email against the ADMIN_EMAILS environment variable.

    Raises:
        HTTPException: 403 Forbidden if user is not an admin.
    """
    settings = get_settings()
    admin_emails = {
        e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()
    }

    if not admin_emails or current_user.email.lower() not in admin_emails:
        logger.warning("Non-admin access attempt: %s", current_user.email)
        _log_admin_security_event(
            "admin_access_denied",
            request=request,
            user_email=current_user.email,
            details={"reason": "User not in admin allowlist"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
