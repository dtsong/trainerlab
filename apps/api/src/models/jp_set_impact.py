"""JP Set Impact model for tracking set releases and meta impact."""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import Date, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class JPSetImpact(Base, TimestampMixin):
    """Track historical set releases and their impact on JP meta.

    Used for predicting EN meta changes when sets release.
    """

    __tablename__ = "jp_set_impacts"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Set identification
    set_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    set_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Release dates
    jp_release_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    en_release_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)

    # Meta snapshots before/after
    # JSON: {"archetype1": 0.15, "archetype2": 0.12, ...}
    jp_meta_before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    jp_meta_after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Key innovations from this set
    # JSON: ["card-id-1", "card-id-2", ...]
    key_innovations: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # New archetypes enabled by this set
    # JSON: ["archetype-id-1", "archetype-id-2", ...]
    new_archetypes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Analysis text
    analysis: Mapped[str | None] = mapped_column(String(5000), nullable=True)
