"""Reserved revision for exercise situation-field ordering.

Revision ID: d3e6a8b2c4f0
Revises: c8d4e1f2a7b9
Create Date: 2026-10-27 14:00:00
"""

revision = "d3e6a8b2c4f0"
down_revision = "c8d4e1f2a7b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The API now controls display order; keep stored field positions unchanged.
    pass


def downgrade() -> None:
    pass
