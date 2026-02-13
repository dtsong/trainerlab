"""Major format windows for official tournament highlighting."""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class MajorFormatWindow(Base, TimestampMixin):
    """Calendar windows for official major format labeling.

    This model is intentionally separate from ``FormatConfig``.
    ``FormatConfig`` drives global rotation UX, while this table captures
    short-lived official-major windows used for roadmap highlighting.
    """

    __tablename__ = "major_format_windows"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    set_range_label: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date_type | None] = mapped_column(Date, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
