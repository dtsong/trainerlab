"""Model for tracking Japanese cards not yet released internationally."""

from uuid import UUID

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class JPUnreleasedCard(Base, TimestampMixin):
    """Japanese cards that haven't been released internationally yet."""

    __tablename__ = "jp_unreleased_cards"

    __table_args__ = (
        CheckConstraint(
            "competitive_impact >= 1 AND competitive_impact <= 5",
            name="ck_competitive_impact_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)

    jp_card_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    jp_set_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    name_jp: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)

    card_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    competitive_impact: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="3"
    )

    affected_archetypes: Mapped[list | None] = mapped_column(
        postgresql.JSONB(), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    expected_release_set: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_released: Mapped[bool] = mapped_column(
        nullable=False, server_default="false", index=True
    )
