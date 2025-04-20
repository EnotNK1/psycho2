"""update_application_table

Revision ID: cac6887fc33c
Revises: c875a3b15feb
Create Date: 2025-04-19 21:40:13.289842

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cac6887fc33c"
down_revision: Union[str, None] = "c875a3b15feb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('inquiry', postgresql.ARRAY(sa.Integer), nullable=True),
        sa.Column('text', sa.String(length=1000), nullable=False),
        sa.Column('status', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('applications')
