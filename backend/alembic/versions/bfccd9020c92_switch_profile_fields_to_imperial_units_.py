"""Switch profile fields to imperial units (lbs, ft, in)

Revision ID: bfccd9020c92
Revises: ff3311a5e5f9
Create Date: 2025-07-10 17:40:01.459094

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bfccd9020c92"
down_revision: Union[str, None] = "ff3311a5e5f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new imperial columns
    op.add_column("profiles", sa.Column("weight_lbs", sa.DECIMAL(5, 2)))
    op.add_column("profiles", sa.Column("height_ft", sa.Integer()))
    op.add_column("profiles", sa.Column("height_in", sa.Integer()))
    # Remove metric columns
    op.drop_column("profiles", "weight_kg")
    op.drop_column("profiles", "height_cm")


def downgrade() -> None:
    # Re-add metric columns
    op.add_column("profiles", sa.Column("weight_kg", sa.DECIMAL(5, 2)))
    op.add_column("profiles", sa.Column("height_cm", sa.Integer()))
    # Remove imperial columns
    op.drop_column("profiles", "weight_lbs")
    op.drop_column("profiles", "height_ft")
    op.drop_column("profiles", "height_in")
