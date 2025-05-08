"""create_applications_table

Revision ID: 46baf81af9c3
Revises: f35a1f11cdf8
Create Date: 2025-04-19 17:19:57.366843

"""
import uuid
import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "46baf81af9c3"
down_revision: Union[str, None] = "f35a1f11cdf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('manager_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('text', sa.String(1000), nullable=False),
        sa.Column('online', sa.Boolean(), default=False),
        sa.Column('problem_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('problem', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.datetime.now),
    )


def downgrade() -> None:
    op.drop_table('applications')
