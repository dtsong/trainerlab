"""Add access grants table.

Revision ID: 034
Revises: 033
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "034"
down_revision: str | None = "033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "access_grants",
        sa.Column("id", sa.UUID(), primary_key=True),
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
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "is_beta_tester",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_subscriber",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by_admin_email", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("email", name="uq_access_grants_email"),
    )

    op.create_index("ix_access_grants_email", "access_grants", ["email"], unique=True)
    op.create_index(
        "ix_access_grants_is_beta_tester",
        "access_grants",
        ["is_beta_tester"],
        unique=False,
    )
    op.create_index(
        "ix_access_grants_is_subscriber",
        "access_grants",
        ["is_subscriber"],
        unique=False,
    )
    op.create_index(
        "ix_access_grants_updated_at",
        "access_grants",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_access_grants_updated_at", table_name="access_grants")
    op.drop_index("ix_access_grants_is_subscriber", table_name="access_grants")
    op.drop_index("ix_access_grants_is_beta_tester", table_name="access_grants")
    op.drop_index("ix_access_grants_email", table_name="access_grants")
    op.drop_table("access_grants")
