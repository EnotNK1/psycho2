"""add link_to_picture in ontology_entry

Revision ID: 6c1f22ec4e53
Revises: 5f66671ae22e
Create Date: 2026-03-26 18:22:08.520787

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6c1f22ec4e53"
down_revision: Union[str, None] = "5f66671ae22e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ontology_entry", sa.Column("link_to_picture", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ontology_entry", "link_to_picture")
