"""add exercise pull group links

Revision ID: c4d9c7b0aa11
Revises: 3f2a8e1b91c4
Create Date: 2026-05-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d9c7b0aa11"
down_revision: Union[str, None] = "3f2a8e1b91c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("field", sa.Column("pull_group", sa.String(), nullable=True))
    op.add_column(
        "filled_field",
        sa.Column("source_group_key", sa.String(), nullable=True),
    )
    op.add_column(
        "filled_field",
        sa.Column("pulled_completed_exercise_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "filled_field",
        sa.Column("pulled_group_key", sa.String(), nullable=True),
    )
    op.add_column(
        "filled_field",
        sa.Column("pulled_fields_snapshot", sa.JSON(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE filled_field
            SET source_group_key = field_id::text
            WHERE source_group_key IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column("filled_field", "pulled_fields_snapshot")
    op.drop_column("filled_field", "pulled_group_key")
    op.drop_column("filled_field", "pulled_completed_exercise_id")
    op.drop_column("filled_field", "source_group_key")
    op.drop_column("field", "pull_group")
