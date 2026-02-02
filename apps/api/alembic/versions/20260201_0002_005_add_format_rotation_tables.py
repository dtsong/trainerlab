"""Add format_configs and rotation_impacts tables.

Revision ID: 005
Revises: 004
Create Date: 2026-02-01

Creates tables for format/rotation management:
- format_configs: Format definitions (legal sets, dates, current/upcoming status)
- rotation_impacts: Per-archetype rotation analysis with survival ratings
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create format_configs table
    op.create_table(
        "format_configs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column(
            "legal_sets",
            postgresql.ARRAY(sa.String(20)),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_upcoming", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "rotation_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
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
    op.create_index("ix_format_configs_name", "format_configs", ["name"])
    op.create_index("ix_format_configs_start_date", "format_configs", ["start_date"])
    op.create_index("ix_format_configs_end_date", "format_configs", ["end_date"])
    op.create_index("ix_format_configs_is_current", "format_configs", ["is_current"])
    op.create_index("ix_format_configs_is_upcoming", "format_configs", ["is_upcoming"])

    # Create rotation_impacts table
    op.create_table(
        "rotation_impacts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("format_transition", sa.String(100), nullable=False),
        sa.Column("archetype_id", sa.String(100), nullable=False),
        sa.Column("archetype_name", sa.String(100), nullable=False),
        sa.Column("survival_rating", sa.String(20), nullable=False),
        sa.Column(
            "rotating_cards",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("analysis", sa.String(5000), nullable=True),
        sa.Column("jp_evidence", sa.String(2000), nullable=True),
        sa.Column("jp_survival_share", sa.Float(), nullable=True),
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
        sa.UniqueConstraint(
            "format_transition", "archetype_id", name="uq_rotation_impact"
        ),
    )
    op.create_index(
        "ix_rotation_impacts_format_transition",
        "rotation_impacts",
        ["format_transition"],
    )
    op.create_index(
        "ix_rotation_impacts_archetype_id", "rotation_impacts", ["archetype_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_rotation_impacts_archetype_id", table_name="rotation_impacts")
    op.drop_index(
        "ix_rotation_impacts_format_transition", table_name="rotation_impacts"
    )
    op.drop_table("rotation_impacts")

    op.drop_index("ix_format_configs_is_upcoming", table_name="format_configs")
    op.drop_index("ix_format_configs_is_current", table_name="format_configs")
    op.drop_index("ix_format_configs_end_date", table_name="format_configs")
    op.drop_index("ix_format_configs_start_date", table_name="format_configs")
    op.drop_index("ix_format_configs_name", table_name="format_configs")
    op.drop_table("format_configs")
