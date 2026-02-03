"""Admin authorization dependency."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status

from src.config import get_settings
from src.dependencies.auth import CurrentUser
from src.models.user import User

logger = logging.getLogger(__name__)


async def require_admin(current_user: CurrentUser) -> User:
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
