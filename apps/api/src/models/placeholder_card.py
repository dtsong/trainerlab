"""Model for storing placeholder cards (unreleased JP cards with translations)."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.card_id_mapping import CardIdMapping


class PlaceholderCard(Base, TimestampMixin):
    """Placeholder cards for unreleased Japanese cards.

    Stores translated English data for unreleased JP cards to enable
    archetype detection and meta analysis before international release.

    Card ID Format: POR-XXX (Perfect Order + random 3-digit number)
    Example: SV10-15 → POR-042
    """

    __tablename__ = "placeholder_cards"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Card identification
    jp_card_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    # Synthetic EN card ID for unreleased cards
    en_card_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )

    # Card names
    name_jp: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)

    # Card attributes
    supertype: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Pokemon, Trainer, Energy
    subtypes: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True
    )  # Basic, Stage 1, V, VSTAR, etc.
    hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    types: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True
    )  # Fire, Water, Lightning, etc.

    # Attacks (for Pokemon cards)
    # Format: [{"name": "...", "cost": [...], "damage": "...", "text": "..."}]
    attacks: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Set information
    set_code: Mapped[str] = mapped_column(
        String(50), nullable=False, default="POR"
    )  # POR = Perfect Order
    official_set_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # ME03

    # Release status
    is_unreleased: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    is_released: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Source tracking
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "limitless", "llm_x", "llm_bluesky", "manual"
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_account: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships (string-based forward reference to avoid circular import)
    card_mappings: Mapped[list["CardIdMapping"]] = relationship(
        "CardIdMapping", back_populates="placeholder_card"
    )

    def __repr__(self) -> str:
        return f"<PlaceholderCard {self.en_card_id}: {self.name_en}>"
