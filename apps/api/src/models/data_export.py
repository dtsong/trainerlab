"""DataExport model for user data exports."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class DataExport(Base, TimestampMixin):
    """User data export request and status tracking."""

    __tablename__ = "data_exports"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    export_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )

    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default={})

    format: Mapped[str] = mapped_column(
        String(20), nullable=False, default="json"
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )

    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
