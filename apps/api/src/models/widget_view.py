"""WidgetView model for widget analytics."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.widget import Widget


class WidgetView(Base):
    """Individual widget view for analytics tracking."""

    __tablename__ = "widget_views"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    widget_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("widgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    widget: Mapped["Widget"] = relationship("Widget", back_populates="views")
