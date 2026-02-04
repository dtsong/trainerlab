"""Model for storing JP-to-EN card ID mappings."""

from uuid import UUID

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class CardIdMapping(Base, TimestampMixin):
    """Mapping between Japanese and English card IDs.

    Japanese card IDs (e.g., "SV7-18") differ from English card IDs
    (e.g., "SCR-28"). This table enables translating JP decklists to
    use EN card IDs for archetype detection via signature cards.
    """

    __tablename__ = "card_id_mappings"

    __table_args__ = (Index("ix_card_id_mappings_en_card_id", "en_card_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)

    jp_card_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    en_card_id: Mapped[str] = mapped_column(String(50), nullable=False)

    card_name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)

    jp_set_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    en_set_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
