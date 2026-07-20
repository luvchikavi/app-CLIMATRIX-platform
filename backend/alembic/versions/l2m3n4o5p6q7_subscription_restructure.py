"""Subscription restructure — add-on caps + Report Pass fields.

The pricing pivot (2026-07-20): the reporting year becomes the unit sold.
- extra_users / extra_sites: purchased add-ons on top of the plan's included
  caps (site packs, seats) — Stripe updates them, super admin can grant them.
- licensed_report_year + plan_expires_at: the one-time Report Pass product —
  Professional-level features for a 90-day window, exports licensed to a
  single reporting year.

NOTE: chained after k1l2m3n4o5p6 (feat/site-grid-region) — that branch must
merge first.

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("extra_users", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "organizations",
        sa.Column("extra_sites", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "organizations",
        sa.Column("licensed_report_year", sa.Integer(), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("plan_expires_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organizations", "plan_expires_at")
    op.drop_column("organizations", "licensed_report_year")
    op.drop_column("organizations", "extra_sites")
    op.drop_column("organizations", "extra_users")
