"""comprehensive baseline - consolidate all add_missing_columns into migration

Revision ID: f1a2b3c4d5e6
Revises: e5f6g7h8i9j0
Create Date: 2026-02-25

This migration consolidates all the column additions that were previously
handled by the add_missing_columns() hack in database.py. It uses
"ADD COLUMN IF NOT EXISTS" so it is safe to run on databases that already
have these columns.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # users
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)"
    )

    # ---------------------------------------------------------------
    # reporting_periods  (verification workflow)
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS status VARCHAR(20)"
    )
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS assurance_level VARCHAR(20)"
    )
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS submitted_by_id UUID"
    )
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE reporting_periods ADD COLUMN IF NOT EXISTS verification_statement TEXT"
    )

    # ---------------------------------------------------------------
    # activities  (data quality - PCAF)
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE activities ADD COLUMN IF NOT EXISTS data_quality_score INTEGER DEFAULT 5"
    )
    op.execute(
        "ALTER TABLE activities ADD COLUMN IF NOT EXISTS data_quality_justification VARCHAR(500)"
    )
    op.execute(
        "ALTER TABLE activities ADD COLUMN IF NOT EXISTS supporting_document_url VARCHAR(500)"
    )

    # ---------------------------------------------------------------
    # cbam_imports
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE cbam_imports ADD COLUMN IF NOT EXISTS sector VARCHAR(20)"
    )

    # ---------------------------------------------------------------
    # emissions  (make emission_factor_id nullable)
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE emissions ALTER COLUMN emission_factor_id DROP NOT NULL"
    )

    # ---------------------------------------------------------------
    # organizations  (Stripe billing / subscription)
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(20) DEFAULT 'free'"
    )
    op.execute(
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20)"
    )
    op.execute(
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP"
    )

    # ---------------------------------------------------------------
    # emission_factors  (governance / approval workflow)
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS previous_version_id UUID"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS change_reason VARCHAR(500)"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS notes VARCHAR(1000)"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS submitted_by_id UUID"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS approved_by_id UUID"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS rejected_by_id UUID"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR(500)"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS created_by_id UUID"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE emission_factors ADD COLUMN IF NOT EXISTS updated_by_id UUID"
    )


def downgrade() -> None:
    # No-op: we cannot safely remove columns from production databases.
    pass
