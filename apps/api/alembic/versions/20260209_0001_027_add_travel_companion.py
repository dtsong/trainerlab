"""Add travel companion: tournament lifecycle, trips, persona

Revision ID: 027
Revises: 026
Create Date: 2026-02-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "027"
down_revision: str | None = "026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tournament lifecycle columns ---
    op.add_column(
        "tournaments",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'completed'"),
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column("city", sa.String(255), nullable=True),
    )
    op.add_column(
        "tournaments",
        sa.Column("venue_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "tournaments",
        sa.Column("venue_address", sa.Text(), nullable=True),
    )
    op.add_column(
        "tournaments",
        sa.Column("registration_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "registration_opens_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "registration_closes_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column("event_source", sa.String(20), nullable=True),
    )
    op.create_index("ix_tournaments_status", "tournaments", ["status"])
    op.create_check_constraint(
        "ck_tournaments_status",
        "tournaments",
        "status IN ('announced', 'registration_open', "
        "'registration_closed', 'active', 'completed')",
    )

    # --- User persona column ---
    op.add_column(
        "users",
        sa.Column("persona", sa.String(20), nullable=True),
    )

    # --- Trips table ---
    op.create_table(
        "trips",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'planning'"),
        ),
        sa.Column(
            "visibility",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "share_token",
            sa.String(36),
            nullable=True,
            unique=True,
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    # --- Trip Events junction table ---
    op.create_table(
        "trip_events",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("trip_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("tournament_id", sa.Uuid(), nullable=False, index=True),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'competitor'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "trip_id",
            "tournament_id",
            name="uq_trip_events_trip_tournament",
        ),
    )


def downgrade() -> None:
    op.drop_table("trip_events")
    op.drop_table("trips")
    op.drop_column("users", "persona")
    op.drop_constraint("ck_tournaments_status", "tournaments", type_="check")
    op.drop_index("ix_tournaments_status", table_name="tournaments")
    op.drop_column("tournaments", "event_source")
    op.drop_column("tournaments", "registration_closes_at")
    op.drop_column("tournaments", "registration_opens_at")
    op.drop_column("tournaments", "registration_url")
    op.drop_column("tournaments", "venue_address")
    op.drop_column("tournaments", "venue_name")
    op.drop_column("tournaments", "city")
    op.drop_column("tournaments", "status")
