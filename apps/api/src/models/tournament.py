"""Tournament model for meta tracking."""

from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.tournament_placement import TournamentPlacement
    from src.models.trip import TripEvent

# Valid tournament lifecycle states
TOURNAMENT_STATUSES = (
    "announced",
    "registration_open",
    "registration_closed",
    "active",
    "completed",
)


class Tournament(Base, TimestampMixin):
    """Pokemon TCG tournament."""

    __tablename__ = "tournaments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('announced', 'registration_open', "
            "'registration_closed', 'active', 'completed')",
            name="ck_tournaments_status",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    # Lifecycle status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed",
        server_default=text("'completed'"),
        index=True,
    )

    # Location/region (NA, EU, JP, LATAM, OCE)
    region: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    venue_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    venue_address: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    # Official major format window metadata (official majors only)
    major_format_key: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    major_format_label: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Registration
    registration_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    registration_opens_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registration_closes_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Source
    source: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # limitless, rk9, etc.
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    event_source: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # pokemon.com, rk9, manual, limitless

    # Relationships
    placements: Mapped[list["TournamentPlacement"]] = relationship(
        "TournamentPlacement",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    trip_events: Mapped[list["TripEvent"]] = relationship(
        "TripEvent",
        back_populates="tournament",
    )
