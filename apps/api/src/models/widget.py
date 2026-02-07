"""Widget model for embeddable creator widgets."""

import secrets
import string
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.widget_view import WidgetView


def generate_widget_id() -> str:
    """Generate a widget ID with w_ prefix + 6 alphanumeric characters."""
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(6))
    return f"w_{suffix}"


class Widget(Base, TimestampMixin):
    """Embeddable widget for creators."""

    __tablename__ = "widgets"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=generate_widget_id
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default={})

    theme: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dark", server_default=text("'dark'")
    )

    accent_color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    show_attribution: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    embed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    view_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="widgets")
    views: Mapped[list["WidgetView"]] = relationship(
        "WidgetView", back_populates="widget", cascade="all, delete-orphan"
    )
