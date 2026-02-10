"""Add CHECK constraints and server defaults for trips

Revision ID: 028
Revises: 027
Create Date: 2026-02-09 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "028"
down_revision: str | None = "027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_trips_status",
        "trips",
        "status IN ('planning','upcoming','active','completed')",
    )
    op.create_check_constraint(
        "ck_trips_visibility",
        "trips",
        "visibility IN ('private','shared')",
    )
    op.create_check_constraint(
        "ck_trip_events_role",
        "trip_events",
        "role IN ('attendee','competitor','judge','spectator')",
    )

    op.alter_column(
        "trips",
        "status",
        server_default="planning",
    )
    op.alter_column(
        "trips",
        "visibility",
        server_default="private",
    )


def downgrade() -> None:
    op.alter_column("trips", "visibility", server_default=None)
    op.alter_column("trips", "status", server_default=None)

    op.drop_constraint("ck_trip_events_role", "trip_events", type_="check")
    op.drop_constraint("ck_trips_visibility", "trips", type_="check")
    op.drop_constraint("ck_trips_status", "trips", type_="check")
