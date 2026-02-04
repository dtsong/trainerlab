"""Creator authorization dependency."""

import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from src.dependencies.auth import CurrentUser
from src.models.user import User

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security.creator")


def _log_creator_security_event(
    event_type: str,
    request: Request | None = None,
    user_email: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a structured security event for creator access."""
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


async def require_creator(request: Request, current_user: CurrentUser) -> User:
    """Verify the current user has creator access.

    Checks the is_creator flag on the user model.

    Raises:
        HTTPException: 403 Forbidden if user is not a creator.
    """
    if not current_user.is_creator:
        logger.warning("Non-creator access attempt: %s", current_user.email)
        _log_creator_security_event(
            "creator_access_denied",
            request=request,
            user_email=current_user.email,
            details={"reason": "User does not have creator flag"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creator access required",
        )

    return current_user


CreatorUser = Annotated[User, Depends(require_creator)]
