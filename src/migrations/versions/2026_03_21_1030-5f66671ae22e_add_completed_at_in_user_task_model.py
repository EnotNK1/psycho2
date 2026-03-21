"""add completed_at in user_task model

Revision ID: 5f66671ae22e
Revises: 5d78feed70e5
Create Date: 2026-03-21 10:30:33.711694

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5f66671ae22e"
down_revision: Union[str, None] = "5d78feed70e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_task", sa.Column("completed_at", sa.DateTime(), nullable=True))



def downgrade() -> None:
    op.drop_column("user_task", "completed_at")