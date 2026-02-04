"""ApiRequest model for API usage tracking."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.api_key import ApiKey


class ApiRequest(Base):
    """Individual API request for analytics and rate limiting."""

    __tablename__ = "api_requests"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    api_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True
    )

    endpoint: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    method: Mapped[str] = mapped_column(String(10), nullable=False)

    status_code: Mapped[int] = mapped_column(Integer, nullable=False)

    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    api_key: Mapped["ApiKey"] = relationship("ApiKey", back_populates="requests")
