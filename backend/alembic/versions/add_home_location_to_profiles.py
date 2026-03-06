"""Add home location fields to profiles

Revision ID: add_home_location_to_profiles
Revises: bb8513bebcd9
Create Date: 2026-03-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_home_location_to_profiles"
down_revision: Union[str, None] = "bb8513bebcd9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("home_lat", sa.Float(), nullable=True))
    op.add_column("profiles", sa.Column("home_lng", sa.Float(), nullable=True))
    op.add_column("profiles", sa.Column("home_address_label", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "home_address_label")
    op.drop_column("profiles", "home_lng")
    op.drop_column("profiles", "home_lat")
