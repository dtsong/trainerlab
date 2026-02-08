"""Model for translated content from Japanese sources."""

from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class TranslatedContent(Base, TimestampMixin):
    """Translated content from Japanese articles and sources."""

    __tablename__ = "translated_content"

    __table_args__ = (
        UniqueConstraint("source_id", "source_url", name="uq_translated_source"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)

    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending", index=True
    )

    uncertainties: Mapped[list | None] = mapped_column(
        postgresql.JSONB(), nullable=True
    )

    translated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Enhanced fields for JP post-rotation intelligence
    title_jp: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_date: Mapped[date_type | None] = mapped_column(
        Date, nullable=True, index=True
    )
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)), nullable=True)
    archetype_refs: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    era_label: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="auto_approved",
    )
