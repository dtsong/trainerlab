"""Card model for Pokemon TCG cards."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.set import Set


class Card(Base, TimestampMixin):
    """Pokemon TCG card."""

    __tablename__ = "cards"

    # Primary key (TCGdex ID, e.g., "sv4-6")
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Basic info
    local_id: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    japanese_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Card type
    supertype: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Pokemon, Trainer, Energy
    subtypes: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )  # Stage 1, ex, V, etc.
    types: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )  # Fire, Water, etc.

    # Pokemon stats
    hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evolves_from: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evolves_to: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(255)), nullable=True
    )

    # Game mechanics (JSON for flexibility)
    attacks: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    abilities: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    weaknesses: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    resistances: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    retreat_cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rules: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Set info
    set_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("sets.id"), nullable=False, index=True
    )
    rarity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Images
    image_small: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_large: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Legality
    regulation_mark: Mapped[str | None] = mapped_column(String(10), nullable=True)
    legalities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Semantic search embedding (pgvector, 1536 dimensions for OpenAI ada-002)
    # Note: Requires pgvector extension. Column added via migration.
    # embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    # Relationships
    set: Mapped["Set"] = relationship("Set", back_populates="cards")
