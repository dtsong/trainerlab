"""FastAPI dependencies for injection."""

from src.dependencies.admin import AdminUser, require_admin
from src.dependencies.api_key_auth import (
    ApiKeyAuth,
    get_api_key_user,
    record_api_request,
)
from src.dependencies.auth import (
    CurrentUser,
    OptionalUser,
    get_current_user,
    get_current_user_optional,
)
from src.dependencies.creator import CreatorUser, require_creator
from src.dependencies.scheduler_auth import verify_scheduler_auth

__all__ = [
    "AdminUser",
    "ApiKeyAuth",
    "CreatorUser",
    "CurrentUser",
    "OptionalUser",
    "get_api_key_user",
    "get_current_user",
    "get_current_user_optional",
    "record_api_request",
    "require_admin",
    "require_creator",
    "verify_scheduler_auth",
]
