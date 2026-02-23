"""Model for external JP meta share data from third-party sources."""

from datetime import date as date_type
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class JPExternalMetaShare(Base, TimestampMixin):
    """Meta share data from external JP sources."""

    __tablename__ = "jp_external_meta_shares"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "report_date",
            "archetype_name_jp",
            name="uq_jp_ext_meta_source_date_arch",
        ),
        CheckConstraint(
            "share_rate >= 0.0 AND share_rate <= 1.0",
            name="ck_share_rate_range",
        ),
        Index(
            "ix_jp_ext_meta_source_date",
            "source",
            "report_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    report_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    archetype_name_jp: Mapped[str] = mapped_column(String(200), nullable=False)
    archetype_name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    share_rate: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
