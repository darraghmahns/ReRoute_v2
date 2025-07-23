"""add_route_models

Revision ID: 1c15fd6e1355
Revises: f1c14c8dc273
Create Date: 2025-07-18 14:16:51.094512

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c15fd6e1355"
down_revision: Union[str, None] = "f1c14c8dc273"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create route tables
    op.create_table(
        "routes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("route_type", sa.String(length=50), nullable=False),
        sa.Column("profile", sa.String(length=50), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=True),
        sa.Column("waypoints", sa.JSON(), nullable=True),
        sa.Column("elevation_profile", sa.JSON(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=False),
        sa.Column("total_elevation_gain_m", sa.Float(), nullable=True),
        sa.Column("total_elevation_loss_m", sa.Float(), nullable=True),
        sa.Column("estimated_time_s", sa.Integer(), nullable=True),
        sa.Column("difficulty_score", sa.Float(), nullable=True),
        sa.Column("start_lat", sa.Float(), nullable=False),
        sa.Column("start_lng", sa.Float(), nullable=False),
        sa.Column("end_lat", sa.Float(), nullable=False),
        sa.Column("end_lng", sa.Float(), nullable=False),
        sa.Column("generation_params", sa.JSON(), nullable=True),
        sa.Column("graphhopper_response", sa.JSON(), nullable=True),
        sa.Column("strava_segments", sa.JSON(), nullable=True),
        sa.Column("popularity_score", sa.Float(), nullable=True),
        sa.Column("is_loop", sa.Boolean(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "route_waypoints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("route_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("elevation_m", sa.Float(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("waypoint_type", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["routes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "saved_routes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("route_id", sa.UUID(), nullable=False),
        sa.Column("saved_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["routes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    pass


def downgrade() -> None:
    # Drop route tables
    op.drop_table("saved_routes")
    op.drop_table("route_waypoints")
    op.drop_table("routes")
