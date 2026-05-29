"""add exercise ordering fields

Revision ID: 3f2a8e1b91c4
Revises: b6f7b1f4d001
Create Date: 2026-05-11 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f2a8e1b91c4"
down_revision: Union[str, None] = "b6f7b1f4d001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercise_structure",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "field",
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        sa.text(
            """
            WITH ordered_exercises AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
                FROM exercise_structure
            )
            UPDATE exercise_structure AS exercise
            SET sort_order = ordered_exercises.rn
            FROM ordered_exercises
            WHERE exercise.id = ordered_exercises.id
            """
        )
    )

    op.execute(
        sa.text(
            """
            WITH ordered_fields AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY exercise_structure_id
                        ORDER BY "order", id
                    ) AS rn
                FROM field
            )
            UPDATE field
            SET position = ordered_fields.rn
            FROM ordered_fields
            WHERE field.id = ordered_fields.id
            """
        )
    )

    op.alter_column("exercise_structure", "sort_order", server_default=None)
    op.alter_column("field", "position", server_default=None)


def downgrade() -> None:
    op.drop_column("field", "position")
    op.drop_column("exercise_structure", "sort_order")
