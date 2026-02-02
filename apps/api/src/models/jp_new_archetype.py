"""JP New Archetype model for tracking JP-only archetypes."""

from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class JPNewArchetype(Base, TimestampMixin):
    """Track entirely new archetypes in JP meta not yet in EN.

    Monitors JP-exclusive archetypes that may preview future EN meta.
    """

    __tablename__ = "jp_new_archetypes"

    __table_args__ = (
        CheckConstraint(
            "jp_meta_share >= 0 AND jp_meta_share <= 1",
            name="ck_jp_archetype_meta_share_range",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Archetype identification
    archetype_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_jp: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Key cards that define this archetype
    # JSON: ["card-id-1", "card-id-2", ...]
    key_cards: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Set that enabled this archetype
    enabled_by_set: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )

    # JP meta performance
    jp_meta_share: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )  # 0.0000-1.0000
    jp_trend: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # rising, stable, falling

    # City League results summary
    # JSON: [{"tournament": "...", "date": "...", "placements": [1, 4, 8]}, ...]
    city_league_results: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Expected EN legality
    estimated_en_legal_date: Mapped[date_type | None] = mapped_column(
        Date, nullable=True
    )

    # Analysis (Research Pass content)
    analysis: Mapped[str | None] = mapped_column(String(5000), nullable=True)
