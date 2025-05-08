"""create_tasks_and_clients_table

Revision ID: f35a1f11cdf8
Revises: 5e526ba7d65e
Create Date: 2025-03-06 01:09:45.265195

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f35a1f11cdf8"
down_revision: Union[str, None] = "5e526ba7d65e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("test_title", sa.String(), nullable=True),
        sa.Column("test_id", sa.UUID(), nullable=True),
        sa.Column("mentor_id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False, default=False),
    )

    # Создание таблицы clients
    op.create_table(
        "clients",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("mentor_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("status", sa.Boolean(), nullable=False, default=False),
    )
