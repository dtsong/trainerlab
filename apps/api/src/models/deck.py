"""Deck model for user deck storage."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.tournament_placement import TournamentPlacement
    from src.models.user import User


class Deck(Base, TimestampMixin):
    """User-created deck."""

    __tablename__ = "decks"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Owner
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Deck info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cards (JSON array: [{"card_id": "sv4-6", "quantity": 4}, ...])
    cards: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=[])

    # Format and archetype
    format: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard"
    )  # standard, expanded
    archetype: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Sharing
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_code: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="decks")
    tournament_placements: Mapped[list["TournamentPlacement"]] = relationship(
        "TournamentPlacement", back_populates="deck"
    )
