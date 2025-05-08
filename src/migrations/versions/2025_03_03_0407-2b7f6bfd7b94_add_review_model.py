"""add review model

Revision ID: 2b7f6bfd7b94
Revises: 02a9ac849076
Create Date: 2025-03-03 04:07:54.475675

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2b7f6bfd7b94"
down_revision: Union[str, None] = "02a9ac849076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("review")
