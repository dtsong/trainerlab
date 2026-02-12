"""Add admin audit events table.

Revision ID: 033
Revises: 032
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "033"
down_revision: str | None = "032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column(
            "actor_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_email", sa.String(length=255), nullable=False),
        sa.Column(
            "target_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
    )

    op.create_index(
        "ix_admin_audit_events_action",
        "admin_audit_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_events_actor_user_id",
        "admin_audit_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_events_actor_email",
        "admin_audit_events",
        ["actor_email"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_events_target_user_id",
        "admin_audit_events",
        ["target_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_events_target_email",
        "admin_audit_events",
        ["target_email"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_events_created_at",
        "admin_audit_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_events_created_at", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_target_email", table_name="admin_audit_events")
    op.drop_index(
        "ix_admin_audit_events_target_user_id", table_name="admin_audit_events"
    )
    op.drop_index("ix_admin_audit_events_actor_email", table_name="admin_audit_events")
    op.drop_index(
        "ix_admin_audit_events_actor_user_id", table_name="admin_audit_events"
    )
    op.drop_index("ix_admin_audit_events_action", table_name="admin_audit_events")
    op.drop_table("admin_audit_events")
