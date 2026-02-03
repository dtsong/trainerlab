"""Add workflow fields to lab_notes and create lab_note_revisions table.

Adds status, version, reviewer_id columns to lab_notes.
Backfills status from is_published.
Creates lab_note_revisions table for revision tracking.

Revision ID: 014
Revises: 013
Create Date: 2026-02-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add workflow fields and create revisions table."""
    # Add workflow columns to lab_notes
    op.add_column(
        "lab_notes",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
    )
    op.add_column(
        "lab_notes",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column(
        "lab_notes",
        sa.Column(
            "reviewer_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Backfill status from is_published
    op.execute("UPDATE lab_notes SET status = 'published' WHERE is_published = true")
    op.execute("UPDATE lab_notes SET status = 'draft' WHERE is_published = false")

    # Add index on status
    op.create_index("ix_lab_notes_status", "lab_notes", ["status"])

    # Create lab_note_revisions table
    op.create_table(
        "lab_note_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "lab_note_id",
            sa.Uuid(),
            sa.ForeignKey("lab_notes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.String(1000), nullable=True),
        sa.Column(
            "author_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("change_description", sa.String(500), nullable=True),
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


def downgrade() -> None:
    """Remove workflow fields and revisions table."""
    op.drop_table("lab_note_revisions")
    op.drop_index("ix_lab_notes_status", table_name="lab_notes")
    op.drop_column("lab_notes", "reviewer_id")
    op.drop_column("lab_notes", "version")
    op.drop_column("lab_notes", "status")
