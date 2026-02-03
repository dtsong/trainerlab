"""LabNote model for content/articles."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class LabNote(Base, TimestampMixin):
    """Lab Note content piece (articles, reports, dispatches).

    Types:
    - weekly_report: Weekly meta analysis
    - jp_dispatch: Japan meta intelligence
    - set_analysis: New set impact analysis
    - rotation_preview: Pre-rotation format preview
    - tournament_recap: Tournament report
    - tournament_preview: Upcoming tournament preview
    - archetype_evolution: Archetype deep dive
    """

    __tablename__ = "lab_notes"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # URL slug for SEO-friendly URLs
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Content type
    note_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # weekly_report, jp_dispatch, etc.

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )  # Short summary for cards/previews
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown content

    # Author info (optional - for guest contributors)
    author_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    author_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Display name override

    # Workflow
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )  # draft, review, published, archived
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reviewer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Publishing (kept for backward compat, synced by service layer)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # SEO / Social
    meta_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    featured_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Tags for filtering/discovery
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)), nullable=True)

    # Related content references
    # JSON: {"archetypes": ["charizard-ex"], "cards": ["sv4-6"], "sets": ["SVI"]}
    related_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Premium content flag (for Research Pass gating)
    is_premium: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
