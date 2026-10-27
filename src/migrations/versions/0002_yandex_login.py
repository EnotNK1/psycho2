"""Attach a Yandex identity without modifying existing accounts or passwords."""

from alembic import op
import sqlalchemy as sa

revision = "compas_0002"
down_revision = "compas_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("yandex_id", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_users_yandex_id", "users", ["yandex_id"])


def downgrade():
    op.drop_constraint("uq_users_yandex_id", "users", type_="unique")
    op.drop_column("users", "yandex_id")
