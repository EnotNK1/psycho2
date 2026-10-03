"""add_diary_mood_tracker_link

Revision ID: a8c4f2d91b30
Revises: 9a1b2c3d4e5f
Create Date: 2026-10-03 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a8c4f2d91b30"
down_revision: Union[str, None] = "9a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diary",
        sa.Column("mood_tracker_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_diary_mood_tracker_id_mood_tracker",
        "diary",
        "mood_tracker",
        ["mood_tracker_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_diary_mood_tracker_id_mood_tracker",
        "diary",
        type_="foreignkey",
    )
    op.drop_column("diary", "mood_tracker_id")
