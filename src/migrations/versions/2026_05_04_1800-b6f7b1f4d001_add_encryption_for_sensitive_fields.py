"""add encryption for sensitive fields

Revision ID: b6f7b1f4d001
Revises: e4b5d0d2bb80
Create Date: 2026-05-04 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.utils.encryption import encrypt_for_storage

# revision identifiers, used by Alembic.
revision: str = "b6f7b1f4d001"
down_revision: Union[str, None] = "e53fd4c3ae68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    scale_result = sa.table(
        "scale_result",
        sa.column("id", sa.Uuid()),
        sa.column("score", sa.Float()),
    )
    filled_field = sa.table(
        "filled_field",
        sa.column("id", sa.Uuid()),
        sa.column("text", sa.Text()),
    )
    mood_tracker = sa.table(
        "mood_tracker",
        sa.column("id", sa.Uuid()),
        sa.column("score", sa.Integer()),
    )
    diary = sa.table(
        "diary",
        sa.column("id", sa.Uuid()),
        sa.column("text", sa.Text()),
    )

    scale_rows = list(bind.execute(sa.select(scale_result.c.id, scale_result.c.score)))
    filled_field_rows = list(bind.execute(sa.select(filled_field.c.id, filled_field.c.text)))
    mood_rows = list(bind.execute(sa.select(mood_tracker.c.id, mood_tracker.c.score)))
    diary_rows = list(bind.execute(sa.select(diary.c.id, diary.c.text)))

    op.alter_column("scale_result", "score", existing_type=sa.Float(), type_=sa.Text(), postgresql_using="score::text")
    op.alter_column("filled_field", "text", existing_type=sa.JSON(), type_=sa.Text(), postgresql_using="text::text")
    op.alter_column("mood_tracker", "score", existing_type=sa.Integer(), type_=sa.Text(), postgresql_using="score::text")
    op.alter_column("diary", "text", existing_type=sa.String(), type_=sa.Text(), postgresql_using="text::text")

    for row_id, score in scale_rows:
        bind.execute(
            sa.text("UPDATE scale_result SET score = :score WHERE id = :id"),
            {"id": row_id, "score": encrypt_for_storage(score)},
        )

    for row_id, text_value in filled_field_rows:
        bind.execute(
            sa.text('UPDATE filled_field SET text = :text WHERE id = :id'),
            {"id": row_id, "text": encrypt_for_storage(text_value)},
        )

    for row_id, score in mood_rows:
        bind.execute(
            sa.text("UPDATE mood_tracker SET score = :score WHERE id = :id"),
            {"id": row_id, "score": encrypt_for_storage(score)},
        )

    for row_id, text_value in diary_rows:
        bind.execute(
            sa.text('UPDATE diary SET text = :text WHERE id = :id'),
            {"id": row_id, "text": encrypt_for_storage(text_value)},
        )


def downgrade() -> None:
    raise RuntimeError("Downgrade is not supported for encrypted sensitive fields.")
