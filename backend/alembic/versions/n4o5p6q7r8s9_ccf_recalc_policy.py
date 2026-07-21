"""CCF completion — base-year recalculation policy threshold.

Adds organizations.recalculation_threshold_pct (GHG Protocol Corporate
Standard ch. 5): the percentage change in base-year emissions from
structural changes (acquisitions, divestments, methodology changes) that
triggers a base-year recalculation. Disclosed in every GHG inventory
report. Existing orgs get the conventional 5% significance threshold.

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "n4o5p6q7r8s9"
down_revision = "m3n4o5p6q7r8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "recalculation_threshold_pct",
            sa.Float(),
            nullable=False,
            server_default="5",
        ),
    )


def downgrade() -> None:
    op.drop_column("organizations", "recalculation_threshold_pct")
