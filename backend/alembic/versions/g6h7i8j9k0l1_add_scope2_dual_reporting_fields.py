"""add scope2 dual reporting fields

Revision ID: g6h7i8j9k0l1
Revises: f1a2b3c4d5e6
Create Date: 2026-03-01

Adds supplier_name and supplier_ef to activities table,
and location_co2e_kg and market_co2e_kg to emissions table
for GHG Protocol Scope 2 dual reporting.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'g6h7i8j9k0l1'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # activities - supplier data persistence
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE activities ADD COLUMN IF NOT EXISTS supplier_name VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE activities ADD COLUMN IF NOT EXISTS supplier_ef NUMERIC"
    )

    # ---------------------------------------------------------------
    # emissions - dual Scope 2 reporting
    # ---------------------------------------------------------------
    op.execute(
        "ALTER TABLE emissions ADD COLUMN IF NOT EXISTS location_co2e_kg NUMERIC"
    )
    op.execute(
        "ALTER TABLE emissions ADD COLUMN IF NOT EXISTS market_co2e_kg NUMERIC"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE emissions DROP COLUMN IF EXISTS market_co2e_kg")
    op.execute("ALTER TABLE emissions DROP COLUMN IF EXISTS location_co2e_kg")
    op.execute("ALTER TABLE activities DROP COLUMN IF EXISTS supplier_ef")
    op.execute("ALTER TABLE activities DROP COLUMN IF EXISTS supplier_name")
