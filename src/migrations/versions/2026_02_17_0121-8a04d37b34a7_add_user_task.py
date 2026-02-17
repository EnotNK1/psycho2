"""add user_task

Revision ID: 8a04d37b34a7
Revises: 621c175953ce
Create Date: 2026-02-17 01:21:51.456406

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8a04d37b34a7"
down_revision: Union[str, None] = "621c175953ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_task",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )



def downgrade() -> None:
    op.drop_table("user_task")
