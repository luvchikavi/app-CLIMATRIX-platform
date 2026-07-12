"""comprehensive baseline - consolidate all add_missing_columns into migration

Revision ID: f1a2b3c4d5e6
Revises: e5f6g7h8i9j0
Create Date: 2026-02-25

This migration consolidates all the column additions that were previously
handled by the add_missing_columns() hack in database.py. On PostgreSQL it
uses "ADD COLUMN IF NOT EXISTS" so it is safe to run on databases that
already have these columns. On SQLite (fresh-DB replays of the full chain,
e.g. dev/test) that syntax doesn't exist, so the same idempotency is
emulated with an inspector check.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e5f6g7h8i9j0"
branch_labels = None
depends_on = None

# (table, column name, SQL type for the PG path, SQLAlchemy column for others)
_COLUMNS: list[tuple[str, str, str, sa.Column]] = [
    ("users", "google_id", "VARCHAR(255)", sa.Column("google_id", sa.String(255))),
    # reporting_periods (verification workflow)
    ("reporting_periods", "status", "VARCHAR(20)", sa.Column("status", sa.String(20))),
    (
        "reporting_periods",
        "assurance_level",
        "VARCHAR(20)",
        sa.Column("assurance_level", sa.String(20)),
    ),
    (
        "reporting_periods",
        "submitted_at",
        "TIMESTAMP",
        sa.Column("submitted_at", sa.DateTime()),
    ),
    (
        "reporting_periods",
        "submitted_by_id",
        "UUID",
        sa.Column("submitted_by_id", sa.Uuid()),
    ),
    (
        "reporting_periods",
        "verified_at",
        "TIMESTAMP",
        sa.Column("verified_at", sa.DateTime()),
    ),
    (
        "reporting_periods",
        "verified_by",
        "VARCHAR(255)",
        sa.Column("verified_by", sa.String(255)),
    ),
    (
        "reporting_periods",
        "verification_statement",
        "TEXT",
        sa.Column("verification_statement", sa.Text()),
    ),
    # activities (data quality - PCAF)
    (
        "activities",
        "data_quality_score",
        "INTEGER DEFAULT 5",
        sa.Column("data_quality_score", sa.Integer(), server_default="5"),
    ),
    (
        "activities",
        "data_quality_justification",
        "VARCHAR(500)",
        sa.Column("data_quality_justification", sa.String(500)),
    ),
    (
        "activities",
        "supporting_document_url",
        "VARCHAR(500)",
        sa.Column("supporting_document_url", sa.String(500)),
    ),
    # cbam_imports
    ("cbam_imports", "sector", "VARCHAR(20)", sa.Column("sector", sa.String(20))),
    # organizations (Stripe billing / subscription)
    (
        "organizations",
        "stripe_customer_id",
        "VARCHAR(255)",
        sa.Column("stripe_customer_id", sa.String(255)),
    ),
    (
        "organizations",
        "stripe_subscription_id",
        "VARCHAR(255)",
        sa.Column("stripe_subscription_id", sa.String(255)),
    ),
    (
        "organizations",
        "subscription_plan",
        "VARCHAR(20) DEFAULT 'free'",
        sa.Column("subscription_plan", sa.String(20), server_default="free"),
    ),
    (
        "organizations",
        "subscription_status",
        "VARCHAR(20)",
        sa.Column("subscription_status", sa.String(20)),
    ),
    (
        "organizations",
        "subscription_current_period_end",
        "TIMESTAMP",
        sa.Column("subscription_current_period_end", sa.DateTime()),
    ),
    (
        "organizations",
        "trial_ends_at",
        "TIMESTAMP",
        sa.Column("trial_ends_at", sa.DateTime()),
    ),
    # emission_factors (governance / approval workflow)
    (
        "emission_factors",
        "status",
        "VARCHAR(20) DEFAULT 'approved'",
        sa.Column("status", sa.String(20), server_default="approved"),
    ),
    (
        "emission_factors",
        "version",
        "INTEGER DEFAULT 1",
        sa.Column("version", sa.Integer(), server_default="1"),
    ),
    (
        "emission_factors",
        "previous_version_id",
        "UUID",
        sa.Column("previous_version_id", sa.Uuid()),
    ),
    (
        "emission_factors",
        "change_reason",
        "VARCHAR(500)",
        sa.Column("change_reason", sa.String(500)),
    ),
    ("emission_factors", "notes", "VARCHAR(1000)", sa.Column("notes", sa.String(1000))),
    (
        "emission_factors",
        "submitted_at",
        "TIMESTAMP",
        sa.Column("submitted_at", sa.DateTime()),
    ),
    (
        "emission_factors",
        "submitted_by_id",
        "UUID",
        sa.Column("submitted_by_id", sa.Uuid()),
    ),
    (
        "emission_factors",
        "approved_at",
        "TIMESTAMP",
        sa.Column("approved_at", sa.DateTime()),
    ),
    (
        "emission_factors",
        "approved_by_id",
        "UUID",
        sa.Column("approved_by_id", sa.Uuid()),
    ),
    (
        "emission_factors",
        "rejected_at",
        "TIMESTAMP",
        sa.Column("rejected_at", sa.DateTime()),
    ),
    (
        "emission_factors",
        "rejected_by_id",
        "UUID",
        sa.Column("rejected_by_id", sa.Uuid()),
    ),
    (
        "emission_factors",
        "rejection_reason",
        "VARCHAR(500)",
        sa.Column("rejection_reason", sa.String(500)),
    ),
    (
        "emission_factors",
        "created_by_id",
        "UUID",
        sa.Column("created_by_id", sa.Uuid()),
    ),
    (
        "emission_factors",
        "updated_at",
        "TIMESTAMP",
        sa.Column("updated_at", sa.DateTime()),
    ),
    (
        "emission_factors",
        "updated_by_id",
        "UUID",
        sa.Column("updated_by_id", sa.Uuid()),
    ),
]


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        # Original production path — byte-identical DDL to what already ran.
        for table, column, pg_type, _ in _COLUMNS:
            op.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {pg_type}"
            )
        op.execute(
            "ALTER TABLE emissions ALTER COLUMN emission_factor_id DROP NOT NULL"
        )
        return

    # Fresh-DB replay on SQLite (dev/test): emulate IF NOT EXISTS via inspection.
    inspector = sa.inspect(bind)
    for table, column, _, column_obj in _COLUMNS:
        existing = {c["name"] for c in inspector.get_columns(table)}
        if column not in existing:
            op.add_column(table, column_obj)

    # emissions.emission_factor_id -> nullable (batch mode: SQLite can't ALTER)
    emission_cols = {c["name"]: c for c in inspector.get_columns("emissions")}
    if not emission_cols["emission_factor_id"]["nullable"]:
        with op.batch_alter_table("emissions") as batch_op:
            batch_op.alter_column(
                "emission_factor_id", existing_type=sa.Uuid(), nullable=True
            )


def downgrade() -> None:
    # No-op: we cannot safely remove columns from production databases.
    pass
