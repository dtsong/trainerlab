"""Model for Japanese card adoption rates."""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Float, Integer, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class JPCardAdoptionRate(Base, TimestampMixin):
    """Japanese meta card adoption rates from sources like Pokecabook."""

    __tablename__ = "jp_card_adoption_rates"

    __table_args__ = (
        CheckConstraint(
            "inclusion_rate >= 0 AND inclusion_rate <= 1",
            name="ck_inclusion_rate_range",
        ),
        CheckConstraint(
            "avg_copies >= 0 AND avg_copies <= 4",
            name="ck_avg_copies_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)

    card_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    card_name_jp: Mapped[str | None] = mapped_column(String(255), nullable=True)
    card_name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)

    inclusion_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_copies: Mapped[float | None] = mapped_column(Float, nullable=True)

    archetype_context: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    period_start: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_data: Mapped[dict | None] = mapped_column(postgresql.JSONB(), nullable=True)
