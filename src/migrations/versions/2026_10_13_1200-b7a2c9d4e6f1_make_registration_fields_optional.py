"""make registration fields optional

Revision ID: b7a2c9d4e6f1
Revises: 2c1d8a7bf873
Create Date: 2026-10-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7a2c9d4e6f1"
down_revision: Union[str, None] = "2c1d8a7bf873"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "city", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "city", existing_type=sa.String(), nullable=False)
