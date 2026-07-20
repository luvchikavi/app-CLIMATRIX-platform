"""Verifier read-only portal — verifier_access grants.

A token-gated, read-only grant that lets an external verifier (VVB/auditor)
review ONE reporting period's inventory + provenance + audit log + evidence,
scoped to one org, no login, no writes. The market-standard "auditor role"
(Salesforce Net Zero Cloud, Workiva) but with our per-line derivation trail.

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "m3n4o5p6q7r8"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "verifier_access",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("reporting_period_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("verifier_email", sa.String(length=255), nullable=False),
        sa.Column("verifier_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["reporting_period_id"], ["reporting_periods.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_verifier_access_token", "verifier_access", ["token"], unique=True
    )
    op.create_index(
        "ix_verifier_access_organization_id", "verifier_access", ["organization_id"]
    )
    op.create_index(
        "ix_verifier_access_reporting_period_id",
        "verifier_access",
        ["reporting_period_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verifier_access_reporting_period_id", table_name="verifier_access"
    )
    op.drop_index("ix_verifier_access_organization_id", table_name="verifier_access")
    op.drop_index("ix_verifier_access_token", table_name="verifier_access")
    op.drop_table("verifier_access")
