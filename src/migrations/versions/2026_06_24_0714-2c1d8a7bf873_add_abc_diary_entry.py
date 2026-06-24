"""add_abc_diary_entry

Revision ID: 2c1d8a7bf873
Revises: 4fd1c6b3a9d2
Create Date: 2026-06-24 07:14:46.350776

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2c1d8a7bf873"
down_revision: Union[str, None] = "4fd1c6b3a9d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "abc_diary_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activating_event", sa.String(), nullable=False),
        sa.Column("beliefs", sa.String(), nullable=False),
        sa.Column("consequences", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )



def downgrade() -> None:
    op.drop_table("abc_diary_entries")
