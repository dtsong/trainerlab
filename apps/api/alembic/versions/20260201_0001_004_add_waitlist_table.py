"""Add waitlist table.

Revision ID: 20260201_0001
Revises: 20260130_0001
Create Date: 2026-02-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision: str = "20260201_0001"
down_revision: str | None = "20260130_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create waitlist table."""
    op.create_table(
        "waitlist",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_waitlist_email", "waitlist", ["email"], unique=True)


def downgrade() -> None:
    """Drop waitlist table."""
    op.drop_index("ix_waitlist_email", table_name="waitlist")
    op.drop_table("waitlist")
