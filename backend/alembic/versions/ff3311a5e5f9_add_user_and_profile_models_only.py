"""Add user and profile models only

Revision ID: ff3311a5e5f9
Revises: 6f75d3b39f79
Create Date: 2025-07-10 17:19:46.537028

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ff3311a5e5f9"
down_revision: Union[str, None] = "6f75d3b39f79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
