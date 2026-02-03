"""Tournament model for meta tracking."""

from datetime import date as date_type
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.tournament_placement import TournamentPlacement


class Tournament(Base, TimestampMixin):
    """Pokemon TCG tournament."""

    __tablename__ = "tournaments"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # Location/region (NA, EU, JP, LATAM, OCE)
    region: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Format
    format: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # standard, expanded
    best_of: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )  # 1 for Japan, 3 for international

    # Stats
    participant_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Tournament tier: major, premier, league
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    # Source
    source: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # limitless, rk9, etc.
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)

    # Relationships
    placements: Mapped[list["TournamentPlacement"]] = relationship(
        "TournamentPlacement", back_populates="tournament", cascade="all, delete-orphan"
    )
