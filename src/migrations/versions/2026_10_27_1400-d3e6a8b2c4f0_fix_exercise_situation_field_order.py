"""Place situation fields first in the two introductory exercises.

Revision ID: d3e6a8b2c4f0
Revises: c8d4e1f2a7b9
Create Date: 2026-10-27 14:00:00
"""

import uuid

from alembic import op
import sqlalchemy as sa


revision = "d3e6a8b2c4f0"
down_revision = "c8d4e1f2a7b9"
branch_labels = None
depends_on = None


# exercise_id, field_id, original position, corrected position
FIELD_POSITIONS = (
    ("5f81cc8b-b057-47cb-96af-a0839d6c0ad9", "300d244f-3ac9-48e0-a962-6655004914e7", 1, 2),
    ("5f81cc8b-b057-47cb-96af-a0839d6c0ad9", "836d8f33-4587-4887-a225-0a6388aea7e2", 2, 3),
    ("5f81cc8b-b057-47cb-96af-a0839d6c0ad9", "682a4479-5693-48ae-abe1-df6b899f08df", 3, 1),
    ("4e3f51e9-aad8-4a13-b4b7-d748e472d394", "8e4e8a0d-d473-46ca-8dec-a6b3ffac69bd", 1, 2),
    ("4e3f51e9-aad8-4a13-b4b7-d748e472d394", "983686f3-83cd-493a-b485-8c428eafaddb", 2, 3),
    ("4e3f51e9-aad8-4a13-b4b7-d748e472d394", "4592b3e9-cbd8-4ec2-bed7-e29015cb4db5", 3, 1),
)


def _set_positions(corrected: bool) -> None:
    field = sa.table(
        "field",
        sa.column("id", sa.Uuid()),
        sa.column("exercise_structure_id", sa.Uuid()),
        sa.column("position", sa.Integer()),
    )
    for exercise_id, field_id, original, updated in FIELD_POSITIONS:
        op.execute(
            field.update()
            .where(
                field.c.id == uuid.UUID(field_id),
                field.c.exercise_structure_id == uuid.UUID(exercise_id),
            )
            .values(position=updated if corrected else original)
        )


def upgrade() -> None:
    _set_positions(corrected=True)


def downgrade() -> None:
    _set_positions(corrected=False)
