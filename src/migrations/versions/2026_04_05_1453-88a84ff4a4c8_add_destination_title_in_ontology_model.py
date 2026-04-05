"""add destination_title in ontology model

Revision ID: 88a84ff4a4c8
Revises: 6c1f22ec4e53
Create Date: 2026-04-05 14:53:38.597800

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "88a84ff4a4c8"
down_revision: Union[str, None] = "6c1f22ec4e53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ontology_entry", sa.Column("destination_title", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ontology_entry", "destination_title")
