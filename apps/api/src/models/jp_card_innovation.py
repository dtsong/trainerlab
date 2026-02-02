"""JP Card Innovation model for tracking new card adoption in JP meta."""

from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class JPCardInnovation(Base, TimestampMixin):
    """Track which new cards see competitive play in Japan.

    Monitors card adoption rates from City Leagues to identify
    which new cards are making an impact before EN gets them.
    """

    __tablename__ = "jp_card_innovations"

    __table_args__ = (
        CheckConstraint(
            "adoption_rate >= 0 AND adoption_rate <= 1",
            name="ck_jp_card_adoption_rate_range",
        ),
        CheckConstraint(
            "competitive_impact_rating >= 1 AND competitive_impact_rating <= 5",
            name="ck_jp_card_impact_rating_range",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Card identification
    card_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    card_name: Mapped[str] = mapped_column(String(255), nullable=False)
    card_name_jp: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Set info
    set_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    set_release_jp: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    set_release_en: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Legality
    is_legal_en: Mapped[bool] = mapped_column(default=False, index=True)

    # Adoption metrics
    adoption_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )  # 0.0000-1.0000
    adoption_trend: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # rising, stable, falling

    # Which archetypes use this card
    # JSON: ["charizard-ex", "lugia-vstar", ...]
    archetypes_using: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Impact rating (1-5 scale, Research Pass analysis)
    competitive_impact_rating: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )

    # Analysis text (Research Pass content)
    impact_analysis: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    # Sample size for adoption rate calculation
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
