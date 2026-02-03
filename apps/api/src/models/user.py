"""User model for authentication."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.deck import Deck


class User(Base, TimestampMixin):
    """Application user (linked to auth provider via NextAuth.js)."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Auth provider ID (e.g., Google OAuth providerAccountId)
    auth_provider_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )

    # Profile
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Preferences (JSON: theme, default_format, etc.)
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default={})

    # Beta access (all users during closed beta; grandfathered when monetizing)
    is_beta_tester: Mapped[bool] = mapped_column(
        default=True, server_default=text("true"), nullable=False
    )

    # Relationships
    decks: Mapped[list["Deck"]] = relationship(
        "Deck", back_populates="user", cascade="all, delete-orphan"
    )
