"""Beta access authorization dependency."""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from src.dependencies.auth import CurrentUser
from src.models.user import User

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security.beta")


def _log_beta_security_event(
    event_type: str,
    request: Request | None = None,
    user_email: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a structured security event for beta access."""
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


async def require_beta(request: Request, current_user: CurrentUser) -> User:
    """Verify the current user has beta access."""
    if not current_user.is_beta_tester:
        logger.warning("Non-beta access attempt: %s", current_user.email)
        _log_beta_security_event(
            "beta_access_denied",
            request=request,
            user_email=current_user.email,
            details={"reason": "User is not in beta allowlist"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Beta access required",
        )

    return current_user


BetaUser = Annotated[User, Depends(require_beta)]
