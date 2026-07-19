"""Add staged_rows.region — row-level factor region for derived quantities.

A derived hotel row carries the STAY country so commit can select that
country's hotel-night factor instead of the org default region's.

Revision ID: i9j0k1l2m3n4
Revises: f0a1b2c3d4e5
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "i9j0k1l2m3n4"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "staged_rows",
        sa.Column("region", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("staged_rows", "region")
