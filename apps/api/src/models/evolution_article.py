"""EvolutionArticle model for archetype evolution content."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.evolution_article_snapshot import EvolutionArticleSnapshot
    from src.models.lab_note import LabNote


class EvolutionArticle(Base, TimestampMixin):
    """Published article about an archetype's evolution over time.

    Links to a series of snapshots to tell the story of how an archetype
    adapted across tournaments. Can optionally link to a LabNote.
    """

    __tablename__ = "evolution_articles"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Archetype identifier (normalized name)
    archetype_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # URL slug
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    introduction: Mapped[str | None] = mapped_column(Text, nullable=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status and publishing
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )  # draft, review, published, archived
    is_premium: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Optional link to a lab note
    lab_note_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lab_notes.id", ondelete="SET NULL"), nullable=True
    )

    # Commerce links for recommended cards/products
    # Format: [{"card_id": "sv4-6", "url": "...", "label": "Buy Charizard ex"}]
    commerce_links: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    # Engagement metrics
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    lab_note: Mapped["LabNote | None"] = relationship("LabNote")
    article_snapshots: Mapped[list["EvolutionArticleSnapshot"]] = relationship(
        "EvolutionArticleSnapshot",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="EvolutionArticleSnapshot.position",
    )
