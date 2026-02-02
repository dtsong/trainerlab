"""Prediction model for tracking prediction accuracy."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class Prediction(Base, TimestampMixin):
    """Track predictions and their outcomes for accuracy measurement.

    Used to build credibility by showing prediction track record.
    """

    __tablename__ = "predictions"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Prediction content
    prediction_text: Mapped[str] = mapped_column(String(2000), nullable=False)

    # What event/date this prediction targets
    target_event: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # e.g., "NAIC 2026", "TEF-POR Meta"

    # Target date for resolution
    target_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    outcome: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # correct, partial, incorrect

    # Confidence level when made
    confidence: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # high, medium, low

    # Category for grouping
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )  # meta, archetype, card, tournament

    # Evidence/reasoning
    reasoning: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Outcome notes (explanation of result)
    outcome_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
