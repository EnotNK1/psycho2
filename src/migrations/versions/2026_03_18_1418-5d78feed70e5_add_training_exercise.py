"""add_training_exercise

Revision ID: 5d78feed70e5
Revises: 7c717d58ba2f
Create Date: 2026-03-18 14:18:07.062365

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5d78feed70e5"
down_revision: Union[str, None] = "7c717d58ba2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # training_exercise
    op.create_table(
        "training_exercise",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("picture_link", sa.String(), nullable=True),
        sa.Column("time_to_read", sa.Integer(), nullable=False),
    )

    # training_question
    op.create_table(
        "training_question",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column(
            "training_exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("training_exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    # training_variant
    op.create_table(
        "training_variant",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("explanation", sa.String(), nullable=False),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("training_question.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    # completed_training_exercise
    op.create_table(
        "completed_training_exercise",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "training_exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("training_exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("training_exercise_id",
                            "user_id", name="uq_exercise_user"),
    )


def downgrade() -> None:
    op.drop_table("completed_training_exercise")
    op.drop_table("training_variant")
    op.drop_table("training_question")
    op.drop_table("training_exercise")
