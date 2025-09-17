"""create emojis table

Revision ID: 6cbef205be69
Revises: 0252bd22d980
Create Date: 2025-09-17
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6cbef205be69"
down_revision: Union[str, None] = "0252bd22d980"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "emojis",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("text", sa.String(length=10), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("emojis")
