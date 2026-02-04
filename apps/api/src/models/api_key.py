"""ApiKey model for creator API access."""

import hashlib
import secrets
import string
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.api_request import ApiRequest
    from src.models.user import User


def generate_api_key() -> str:
    """Generate a new API key (prefix_secret format)."""
    chars = string.ascii_letters + string.digits
    prefix = "tl_"
    secret = "".join(secrets.choice(chars) for _ in range(32))
    return f"{prefix}{secret}"


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_key_prefix(key: str) -> str:
    """Get the display prefix of an API key (first 7 chars + last 4)."""
    return f"{key[:7]}...{key[-4:]}"


class ApiKey(Base, TimestampMixin):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    key_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )

    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    monthly_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1000, server_default=text("1000")
    )

    requests_this_month: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    requests: Mapped[list["ApiRequest"]] = relationship(
        "ApiRequest", back_populates="api_key", cascade="all, delete-orphan"
    )
