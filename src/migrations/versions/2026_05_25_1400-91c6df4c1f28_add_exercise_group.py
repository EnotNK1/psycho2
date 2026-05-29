"""add exercise group

Revision ID: 91c6df4c1f28
Revises: c4d9c7b0aa11
Create Date: 2026-05-25 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91c6df4c1f28"
down_revision: Union[str, None] = "c4d9c7b0aa11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercise_structure",
        sa.Column("group", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("exercise_structure", "group", server_default=None)


def downgrade() -> None:
    op.drop_column("exercise_structure", "group")
