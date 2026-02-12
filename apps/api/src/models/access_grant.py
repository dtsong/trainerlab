"""Email-based access grants.

Used to grant beta/subscriber access before a user has logged in (no users row
yet). Grants never expire unless revoked.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin


class AccessGrant(Base, TimestampMixin):
    __tablename__ = "access_grants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    is_beta_tester: Mapped[bool] = mapped_column(
        default=False, server_default=text("false"), nullable=False
    )
    is_subscriber: Mapped[bool] = mapped_column(
        default=False, server_default=text("false"), nullable=False
    )

    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_admin_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
