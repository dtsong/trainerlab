"""FastAPI dependencies for injection."""

from src.dependencies.admin import AdminUser, require_admin
from src.dependencies.auth import (
    CurrentUser,
    OptionalUser,
    get_current_user,
    get_current_user_optional,
)
from src.dependencies.scheduler_auth import verify_scheduler_auth

__all__ = [
    "AdminUser",
    "CurrentUser",
    "OptionalUser",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "verify_scheduler_auth",
]
