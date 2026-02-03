"""ArchetypePrediction model for forecasting archetype performance."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.tournament import Tournament


class ArchetypePrediction(Base, TimestampMixin):
    """Prediction for an archetype's performance at an upcoming tournament.

    Stores predicted meta share, day 2 rate, tier, and likely adaptations.
    After the tournament, actual results are backfilled for accuracy scoring.
    """

    __tablename__ = "archetype_predictions"
    __table_args__ = (
        UniqueConstraint(
            "archetype_id",
            "target_tournament_id",
            name="uq_prediction_archetype_tournament",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Archetype identifier (normalized name)
    archetype_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Target tournament
    target_tournament_id: Mapped[UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Predictions (ranges stored as JSON: {"low": 0.05, "mid": 0.08, "high": 0.12})
    predicted_meta_share: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    predicted_day2_rate: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    predicted_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Expected adaptations and signals
    # Format: [{"type": "tech", "description": "...", "cards": [...]}]
    likely_adaptations: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    # Format: {"trending_in_jp": true, "jp_meta_share": 0.15, ...}
    jp_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Confidence and methodology
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Actuals (backfilled after tournament)
    actual_meta_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    target_tournament: Mapped["Tournament"] = relationship("Tournament")
