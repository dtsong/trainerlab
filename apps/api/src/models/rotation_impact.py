"""RotationImpact model for per-archetype rotation analysis."""

from uuid import UUID

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class RotationImpact(Base, TimestampMixin):
    """Per-archetype rotation analysis.

    Tracks how each archetype is affected by a format transition,
    including which cards rotate, survival ratings, and JP evidence.
    """

    __tablename__ = "rotation_impacts"

    __table_args__ = (
        UniqueConstraint(
            "format_transition", "archetype_id", name="uq_rotation_impact"
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Format transition (e.g., "svi-asc-to-tef-por")
    format_transition: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    # Archetype reference (matches archetype names in MetaSnapshot)
    archetype_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g., "charizard-ex", "lugia-vstar"
    archetype_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "Charizard ex", "Lugia VSTAR"

    # Survival rating
    # dies: loses core cards, unplayable
    # crippled: major losses, significantly weaker
    # adapts: loses some cards but has replacements
    # thrives: minimal losses or gains from new set
    # unknown: insufficient data to assess
    survival_rating: Mapped[str] = mapped_column(String(20), nullable=False)

    # Rotating cards with details
    # JSON array: [{"card_name": "Lumineon V", "card_id": "brs-40", "count": 1,
    #               "role": "search", "replacement": "Snorlax"}, ...]
    rotating_cards: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Analysis text (Research Pass content)
    analysis: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    # Japan evidence (they've been playing post-rotation format)
    jp_evidence: Mapped[str | None] = mapped_column(
        String(2000), nullable=True
    )  # What we learned from JP meta
    jp_survival_share: Mapped[float | None] = mapped_column(
        nullable=True
    )  # Meta share in JP post-rotation (0.0-1.0)
