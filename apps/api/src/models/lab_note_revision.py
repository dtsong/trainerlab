"""LabNoteRevision model for revision tracking."""

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class LabNoteRevision(Base, TimestampMixin):
    """Tracks content revisions for lab notes."""

    __tablename__ = "lab_note_revisions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    lab_note_id: Mapped[UUID] = mapped_column(
        ForeignKey("lab_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    author_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    change_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
