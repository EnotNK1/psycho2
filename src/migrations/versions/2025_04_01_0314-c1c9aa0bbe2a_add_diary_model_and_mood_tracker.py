"""add diary model and mood tracker

 Revision ID: c1c9aa0bbe2a
 Revises: 2b7f6bfd7b94
 Create Date: 2025-04-01 03:14:35.531830

 """

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1c9aa0bbe2a"
down_revision: Union[str, None] = "2b7f6bfd7b94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "diary",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_diary_user_id"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "mood_tracker",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_mood_tracker_user_id"),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.drop_table("mood_tracker")
    op.drop_table("diary")