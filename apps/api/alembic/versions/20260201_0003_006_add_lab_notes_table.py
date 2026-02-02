"""Add lab_notes table.

Revision ID: 006
Revises: 005
Create Date: 2026-02-01

Creates lab_notes table for content management:
- Articles, weekly reports, JP dispatches, set analyses
- Markdown content with metadata
- Premium content gating support
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lab_notes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("note_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.String(1000), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "author_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("author_name", sa.String(255), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, default=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta_description", sa.String(300), nullable=True),
        sa.Column("featured_image_url", sa.String(500), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column(
            "related_content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("is_premium", sa.Boolean(), nullable=False, default=False),
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
    op.create_index("ix_lab_notes_slug", "lab_notes", ["slug"])
    op.create_index("ix_lab_notes_note_type", "lab_notes", ["note_type"])
    op.create_index("ix_lab_notes_author_id", "lab_notes", ["author_id"])
    op.create_index("ix_lab_notes_is_published", "lab_notes", ["is_published"])
    op.create_index("ix_lab_notes_published_at", "lab_notes", ["published_at"])
    op.create_index("ix_lab_notes_is_premium", "lab_notes", ["is_premium"])


def downgrade() -> None:
    op.drop_index("ix_lab_notes_is_premium", table_name="lab_notes")
    op.drop_index("ix_lab_notes_published_at", table_name="lab_notes")
    op.drop_index("ix_lab_notes_is_published", table_name="lab_notes")
    op.drop_index("ix_lab_notes_author_id", table_name="lab_notes")
    op.drop_index("ix_lab_notes_note_type", table_name="lab_notes")
    op.drop_index("ix_lab_notes_slug", table_name="lab_notes")
    op.drop_table("lab_notes")
