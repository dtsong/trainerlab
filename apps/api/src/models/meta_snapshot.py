"""MetaSnapshot model for computed meta data."""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import Date, Integer, String, UniqueConstraint
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
