"""add_training_plans_table

Revision ID: f1c14c8dc273
Revises: bfccd9020c92
Create Date: 2025-07-16 17:35:00.808511

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1c14c8dc273"
down_revision: Union[str, None] = "add_password_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create training_plans table
    op.create_table(
        "training_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("goal", sa.String(), nullable=True),
        sa.Column("weekly_hours", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("plan_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_training_plans_user_id"), "training_plans", ["user_id"], unique=False
    )


def downgrade() -> None:
    # Drop training_plans table
    op.drop_index(op.f("ix_training_plans_user_id"), table_name="training_plans")
    op.drop_table("training_plans")
