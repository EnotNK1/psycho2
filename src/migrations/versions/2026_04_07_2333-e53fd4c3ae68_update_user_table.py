"""update user table

Revision ID: e53fd4c3ae68
Revises: 88a84ff4a4c8
Create Date: 2026-04-07 23:33:17.994238

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e53fd4c3ae68"
down_revision: Union[str, None] = "e4b5d0d2bb80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_inquiry",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("inquiry_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["inquiry_id"],
            ["inquiry.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "inquiry_id"),
    )

    op.add_column(
        "users",
        sa.Column("higher_education_university", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "higher_education_specialization", sa.String(length=255), nullable=True
        ),
    )
    op.add_column(
        "users", sa.Column("academic_degree", sa.String(length=100), nullable=True)
    )
    op.add_column("users", sa.Column("courses", sa.String(length=400), nullable=True))
    op.add_column(
        "users", sa.Column("work_format", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "users", sa.Column("association", sa.String(length=200), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "association")
    op.drop_column("users", "work_format")
    op.drop_column("users", "courses")
    op.drop_column("users", "academic_degree")
    op.drop_column("users", "higher_education_specialization")
    op.drop_column("users", "higher_education_university")


    op.drop_table("user_inquiry")

