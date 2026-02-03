"""Adaptation model for tracking changes between archetype snapshots."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot


class Adaptation(Base, TimestampMixin):
    """A specific adaptation detected between two archetype snapshots.

    Records cards added/removed, the type of adaptation, and what
    archetype it targets (if a tech choice).
    """

    __tablename__ = "adaptations"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Parent snapshot
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("archetype_evolution_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Adaptation details
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # tech, consistency, engine, removal
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Card changes
    # Format: [{"card_id": "sv4-6", "name": "Charizard ex", "quantity": 2}]
    cards_added: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    cards_removed: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # What this adaptation targets (e.g., "Dragapult ex" if teching against it)
    target_archetype: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # How widespread and confident the detection is
    prevalence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Source of classification (diff, claude, manual)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    snapshot: Mapped["ArchetypeEvolutionSnapshot"] = relationship(
        "ArchetypeEvolutionSnapshot", back_populates="adaptations"
    )
