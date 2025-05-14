"""create_clients_and_tasks_tables

Revision ID: f5134ac574c3
Revises: 319e208e960a
Create Date: 2025-05-15 05:50:06.916167

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f5134ac574c3"
down_revision: Union[str, None] = "319e208e960a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Создание таблицы Clients
    op.create_table(
        'clients',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('client_id', sa.Uuid(), nullable=False),
        sa.Column('mentor_id', sa.Uuid(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('status', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание таблицы Tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('test_title', sa.String(), nullable=True),
        sa.Column('test_id', sa.Uuid(), nullable=True),
        sa.Column('mentor_id', sa.Uuid(), nullable=False),
        sa.Column('client_id', sa.Uuid(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['mentor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Можно добавить индексы для улучшения производительности
    op.create_index(op.f('ix_clients_client_id'), 'clients', ['client_id'], unique=False)
    op.create_index(op.f('ix_clients_mentor_id'), 'clients', ['mentor_id'], unique=False)
    op.create_index(op.f('ix_tasks_mentor_id'), 'tasks', ['mentor_id'], unique=False)
    op.create_index(op.f('ix_tasks_client_id'), 'tasks', ['client_id'], unique=False)


def downgrade():
    # Удаление индексов сначала
    op.drop_index(op.f('ix_tasks_client_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_mentor_id'), table_name='tasks')
    op.drop_index(op.f('ix_clients_mentor_id'), table_name='clients')
    op.drop_index(op.f('ix_clients_client_id'), table_name='clients')

    # Удаление таблиц
    op.drop_table('tasks')
    op.drop_table('clients')