"""add avatar link to users

Revision ID: 4fd1c6b3a9d2
Revises: 91c6df4c1f28
Create Date: 2026-06-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4fd1c6b3a9d2"
down_revision: Union[str, None] = "91c6df4c1f28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_link", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_link")
