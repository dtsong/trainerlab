"""ArchetypeSprite model for sprite-key to archetype mapping."""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class ArchetypeSprite(Base, TimestampMixin):
    """Maps a sprite key to its canonical archetype name."""

    __tablename__ = "archetype_sprites"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    sprite_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    archetype_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sprite_urls: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    pokemon_names: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
