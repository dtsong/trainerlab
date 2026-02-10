"""Trip and TripEvent models for travel companion."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.tournament import Tournament
    from src.models.user import User


class Trip(Base, TimestampMixin):
    """A user's trip plan containing one or more events."""

    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planning','upcoming','active','completed')",
            name="ck_trips_status",
        ),
        CheckConstraint(
            "visibility IN ('private','shared')",
            name="ck_trips_visibility",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Owner
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Trip info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="planning",
        server_default="planning",
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="private",
        server_default="private",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sharing
    share_token: Mapped[str | None] = mapped_column(
        String(36), unique=True, nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trips")
    trip_events: Mapped[list["TripEvent"]] = relationship(
        "TripEvent",
        back_populates="trip",
        cascade="all, delete-orphan",
    )


class TripEvent(Base):
    """Junction table linking trips to tournaments/events."""

    __tablename__ = "trip_events"
    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "tournament_id",
            name="uq_trip_events_trip_tournament",
        ),
        CheckConstraint(
            "role IN ('attendee','competitor','judge','spectator')",
            name="ck_trip_events_role",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Foreign keys
    trip_id: Mapped[UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tournament_id: Mapped[UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event-specific info
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="competitor"
    )  # attendee, competitor, judge, spectator
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="trip_events")
    tournament: Mapped["Tournament"] = relationship(
        "Tournament", back_populates="trip_events"
    )
