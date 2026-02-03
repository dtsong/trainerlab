"""ArchetypeEvolutionSnapshot model for tracking archetype performance over time."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.adaptation import Adaptation
    from src.models.evolution_article_snapshot import EvolutionArticleSnapshot
    from src.models.tournament import Tournament


class ArchetypeEvolutionSnapshot(Base, TimestampMixin):
    """Snapshot of an archetype's performance at a specific tournament.

    Captures meta share, top cut conversion, consensus decklist, and
    card usage data for tracking how an archetype evolves over time.
    """

    __tablename__ = "archetype_evolution_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "archetype", "tournament_id", name="uq_snapshot_archetype_tournament"
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Archetype identifier (normalized name)
    archetype: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Tournament reference
    tournament_id: Mapped[UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Performance metrics
    meta_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_cut_conversion: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_placement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deck_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Consensus decklist and card usage (JSONB)
    # [{"card_id": "...", "name": "...", "quantity": N, "inclusion_rate": 0.95}]
    consensus_list: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    # {"card_name": {"name": "...", "avg_count": 2.8, "inclusion_rate": 0.95}}
    card_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Optional context notes
    meta_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    tournament: Mapped["Tournament"] = relationship("Tournament")
    adaptations: Mapped[list["Adaptation"]] = relationship(
        "Adaptation", back_populates="snapshot", cascade="all, delete-orphan"
    )
    article_snapshots: Mapped[list["EvolutionArticleSnapshot"]] = relationship(
        "EvolutionArticleSnapshot",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )
