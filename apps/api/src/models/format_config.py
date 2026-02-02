"""FormatConfig model for format management and rotation tracking."""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import Boolean, Date, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class FormatConfig(Base, TimestampMixin):
    """Format configuration for a specific legal set range.

    Drives all format-dependent UI and rotation tracking.
    Examples: SVI-ASC (current), TEF-POR (upcoming after April 10 rotation)
    """

    __tablename__ = "format_configs"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Format identification
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )  # e.g., "svi-asc", "tef-por"
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "SVI-ASC", "TEF-POR"

    # Legal sets (array of set codes)
    legal_sets: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)), nullable=False
    )  # e.g., ["SVI", "PAL", "OBF", "MEW", ...]

    # Format lifecycle
    start_date: Mapped[date_type | None] = mapped_column(
        Date, nullable=True, index=True
    )  # When this format becomes legal
    end_date: Mapped[date_type | None] = mapped_column(
        Date, nullable=True, index=True
    )  # When this format rotates out

    # Status flags
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    is_upcoming: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # Rotation details (only populated for upcoming formats)
    # JSON: {"rotating_out_sets": ["SVI", "PAL", ...], "new_set": "POR"}
    rotation_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
