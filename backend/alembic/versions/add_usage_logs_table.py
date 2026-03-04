"""Add usage_logs table for tier enforcement

Revision ID: add_usage_logs_table
Revises: add_home_location_to_profiles
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_usage_logs_table"
down_revision: Union[str, None] = "add_subscriptions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("feature", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"], unique=False)
    op.create_index("ix_usage_logs_timestamp", "usage_logs", ["timestamp"], unique=False)
    op.create_index(
        "ix_usage_logs_user_feature_timestamp",
        "usage_logs",
        ["user_id", "feature", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_usage_logs_user_feature_timestamp", table_name="usage_logs")
    op.drop_index("ix_usage_logs_timestamp", table_name="usage_logs")
    op.drop_index("ix_usage_logs_user_id", table_name="usage_logs")
    op.drop_table("usage_logs")
