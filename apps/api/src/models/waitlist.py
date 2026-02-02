"""Waitlist model for email capture."""

from uuid import UUID, uuid4

from sqlalchemy import String
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
