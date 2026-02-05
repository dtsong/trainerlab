"""Model for storing JP-to-EN card ID mappings."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.placeholder_card import PlaceholderCard


class CardIdMapping(Base, TimestampMixin):
    """Mapping between Japanese and English card IDs.

    Japanese card IDs (e.g., "SV7-18") differ from English card IDs
    (e.g., "SCR-28"). This table enables translating JP decklists to
    use EN card IDs for archetype detection via signature cards.

    Also supports synthetic mappings for unreleased cards using
    placeholder card IDs (e.g., "POR-042").
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

    # Track if this is a synthetic mapping for unreleased cards
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Link to placeholder card details (if synthetic)
    placeholder_card_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("placeholder_cards.id"), nullable=True, index=True
    )

    # Relationships
    placeholder_card: Mapped["PlaceholderCard | None"] = relationship(
        "PlaceholderCard", back_populates="card_mappings"
    )
