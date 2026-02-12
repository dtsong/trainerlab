"""Extend waitlist to support request access context.

Revision ID: 035
Revises: 034
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "035"
down_revision: str | None = "034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("waitlist", sa.Column("note", sa.Text(), nullable=True))
    op.add_column("waitlist", sa.Column("intent", sa.String(length=32), nullable=True))
    op.add_column("waitlist", sa.Column("source", sa.String(length=64), nullable=True))
    op.add_column(
        "waitlist",
        sa.Column(
            "request_count",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )

    op.create_index("ix_waitlist_intent", "waitlist", ["intent"], unique=False)
    op.create_index("ix_waitlist_source", "waitlist", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_waitlist_source", table_name="waitlist")
    op.drop_index("ix_waitlist_intent", table_name="waitlist")
    op.drop_column("waitlist", "request_count")
    op.drop_column("waitlist", "source")
    op.drop_column("waitlist", "intent")
    op.drop_column("waitlist", "note")
