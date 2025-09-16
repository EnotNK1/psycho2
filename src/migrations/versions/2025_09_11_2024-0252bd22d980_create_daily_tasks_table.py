"""create_daily_tasks_table

Revision ID: 0252bd22d980
Revises: 01b758f30467
Create Date: 2025-09-11 20:24:27.950398

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0252bd22d980"
down_revision: Union[str, None] = "01b758f30467"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.execute("DROP TYPE IF EXISTS dailytasktype")

    op.create_table(
        'daily_task',
        sa.Column('id', sa.dialects.postgresql.UUID(),
                 nullable=False,
                 server_default=sa.text('gen_random_uuid()')),  # Добавьте это
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('short_desc', sa.String(), nullable=False),
        sa.Column('destination_id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column(
            'type',
            sa.Enum('THEORY', 'MOOD_TRACKER_AND_FREE_DIARY', 'TEST', 'OTHER', name='dailytasktype'),
            nullable=False
        ),
        sa.Column('user_id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )



def downgrade() -> None:
    op.drop_table('daily_task')
    op.execute("DROP TYPE IF EXISTS dailytasktype")