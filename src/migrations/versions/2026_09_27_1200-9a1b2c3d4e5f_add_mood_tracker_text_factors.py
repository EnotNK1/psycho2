"""add_mood_tracker_text_factors

Revision ID: 9a1b2c3d4e5f
Revises: 2c1d8a7bf873
Create Date: 2026-09-27 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9a1b2c3d4e5f"
down_revision: Union[str, None] = "2c1d8a7bf873"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mood_tracker",
        sa.Column("emotions", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "mood_tracker",
        sa.Column("influence_factors", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("mood_tracker", "influence_factors")
    op.drop_column("mood_tracker", "emotions")
