"""TournamentPlacement model for tournament results."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.deck import Deck
    from src.models.tournament import Tournament


class TournamentPlacement(Base, TimestampMixin):
    """A deck's placement in a tournament."""

    __tablename__ = "tournament_placements"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Tournament reference
    tournament_id: Mapped[UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Deck reference (nullable - not all placements have full deck lists)
    deck_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("decks.id", ondelete="SET NULL"), nullable=True
    )

    # Placement info
    placement: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    player_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Archetype (even if no full deck list)
    archetype: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Deck list (JSON if available, for tournament-specific lists)
    decklist: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    decklist_source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    tournament: Mapped["Tournament"] = relationship(
        "Tournament", back_populates="placements"
    )
    deck: Mapped["Deck | None"] = relationship(
        "Deck", back_populates="tournament_placements"
    )
