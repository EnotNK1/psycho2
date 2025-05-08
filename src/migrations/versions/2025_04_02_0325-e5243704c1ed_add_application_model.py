"""add application model

Revision ID: e5243704c1ed
Revises: c1c9aa0bbe2a
Create Date: 2025-04-02 03:25:36.437411

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5243704c1ed"
down_revision: Union[str, None] = "c1c9aa0bbe2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("manager_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(length=1000), nullable=False),
        sa.Column("online", sa.Boolean(), nullable=False, default=False),
        sa.Column("problem_id", sa.Uuid(), nullable=True),
        sa.Column("problem", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], name="fk_applications_client_id"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], name="fk_applications_manager_id"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("applications")
