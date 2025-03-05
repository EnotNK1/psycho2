"""create_test_models

Revision ID: eb8039c1ebac
Revises: 02a9ac849076
Create Date: 2025-02-27 20:31:09.345278

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eb8039c1ebac"
down_revision: Union[str, None] = "02a9ac849076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "test",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("short_desc", sa.String(), nullable=False),
        sa.Column("link", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "question",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["test.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scale",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("min", sa.Integer(), nullable=False),
        sa.Column("max", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["test.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "test_result.py",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["test.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "answer_choice",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["question.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "borders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("left_border", sa.Float(), nullable=False),
        sa.Column("right_border", sa.Float(), nullable=False),
        sa.Column("color", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("user_recommendation", sa.String(), nullable=True),
        sa.Column("scale_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["scale_id"], ["scale.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scale_result",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("scale_id", sa.Uuid(), nullable=False),
        sa.Column("test_result_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["scale_id"], ["scale.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["test_result_id"], ["test_result.py.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("scale_result")
    op.drop_table("borders")
    op.drop_table("answer_choice")
    op.drop_table("test_result.py")
    op.drop_table("scale")
    op.drop_table("question")
    op.drop_table("test")
    # ### end Alembic commands ###
