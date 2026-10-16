"""merge migration heads

Revision ID: c8d4e1f2a7b9
Revises: a8c4f2d91b30, b7a2c9d4e6f1
Create Date: 2026-10-16 12:00:00.000000

"""

from typing import Sequence, Union


revision: str = "c8d4e1f2a7b9"
down_revision: Union[str, Sequence[str], None] = ("a8c4f2d91b30", "b7a2c9d4e6f1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
