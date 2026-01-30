"""Set model for Pokemon TCG card sets."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.card import Card


class Set(Base, TimestampMixin):
    """Pokemon TCG card set."""

    __tablename__ = "sets"

    # Primary key (TCGdex ID, e.g., "sv4")
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    series: Mapped[str] = mapped_column(String(255), nullable=False)

    # Release info
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    release_date_jp: Mapped[date | None] = mapped_column(Date, nullable=True)
    card_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Images
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    symbol_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Legalities (JSON: {"standard": "Legal", "expanded": "Legal"})
    legalities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    cards: Mapped[list["Card"]] = relationship("Card", back_populates="set")
