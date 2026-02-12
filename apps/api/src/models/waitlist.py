"""Waitlist model for email capture.

Used for launch updates and closed beta access requests.
"""

from uuid import UUID, uuid4

from sqlalchemy import Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class WaitlistEntry(Base, TimestampMixin):
    """Email waitlist entry for Research Pass."""

    __tablename__ = "waitlist"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Email (unique to prevent duplicates)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Optional context (first note is preserved; repeats only increment count)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    request_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
    )
