"""add test_type and opposite_text

Revision ID: 621c175953ce
Revises: b6112f6bbda1
Create Date: 2026-01-21 19:31:04.355111

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "621c175953ce"
down_revision: Union[str, None] = "b6112f6bbda1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "question", sa.Column("opposite_text", sa.String(), nullable=True)
    )
    op.add_column("test", sa.Column("type", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("test", "type")
    op.drop_column("question", "opposite_text")
