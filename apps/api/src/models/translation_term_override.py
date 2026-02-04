"""Model for user-defined translation term overrides."""

from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class TranslationTermOverride(Base, TimestampMixin):
    """Custom translation overrides that take precedence over the static glossary."""

    __tablename__ = "translation_term_overrides"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    term_jp: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    term_en: Mapped[str] = mapped_column(String(255), nullable=False)

    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        nullable=False, server_default="true", index=True
    )
