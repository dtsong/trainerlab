"""MetaSnapshot model for computed meta data."""

from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class MetaSnapshot(Base, TimestampMixin):
    """Computed meta snapshot for a specific date/region/format."""

    __tablename__ = "meta_snapshots"

    # Unique constraint on snapshot dimensions
    __table_args__ = (
        UniqueConstraint(
            "snapshot_date", "region", "format", "best_of", name="uq_meta_snapshot"
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Snapshot dimensions
    snapshot_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )  # null = global
    format: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # standard, expanded
    best_of: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )  # 1 for Japan, 3 for international

    # Archetype breakdown (JSON: {"Charizard ex": 0.15, "Lugia VSTAR": 0.12, ...})
    archetype_shares: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Card usage rates (JSON: {"sv4-6": {"inclusion_rate": 0.85, ...}, ...})
    card_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Sample info
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    tournaments_included: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Enhanced meta analysis (added in migration 004)
    # Simpson's diversity index: 1 - sum(share^2), range 0-1 (higher = more diverse)
    diversity_index: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True
    )

    # Tier assignments: {"Charizard ex": "S", "Gardevoir ex": "A", ...}
    # Tiers: S (>15%), A (8-15%), B (3-8%), C (1-3%), Rogue (<1%)
    tier_assignments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # JP signals: divergence between JP (BO1) and EN (BO3) meta
    # {"rising": ["Archetype1"], "falling": ["Archetype2"], "divergent": [...]}
    jp_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Week-over-week trends: {"Charizard ex": {"change": 0.02, "direction": "up"}, ...}
    trends: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
