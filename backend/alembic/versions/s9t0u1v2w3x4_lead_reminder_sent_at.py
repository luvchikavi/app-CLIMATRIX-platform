"""Uncontacted-lead reminder stamp.

The background sweep reminds the founder once about each lead still sitting
in "new" after the reminder window; the stamp is what makes it once.

Revision ID: s9t0u1v2w3x4
Revises: r8s9t0u1v2w3
Create Date: 2026-07-24
"""

import sqlalchemy as sa
from alembic import op

revision = "s9t0u1v2w3x4"
down_revision = "r8s9t0u1v2w3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("reminder_sent_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("leads", "reminder_sent_at")
