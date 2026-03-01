"""add scope2 dual reporting fields

Revision ID: g6h7i8j9k0l1
Revises: f1a2b3c4d5e6
Create Date: 2026-03-01

Adds supplier_name and supplier_ef to activities table,
and location_co2e_kg and market_co2e_kg to emissions table
for GHG Protocol Scope 2 dual reporting.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'g6h7i8j9k0l1'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def _add_column_if_not_exists(table: str, column_name: str, column_type):
    """Add a column, silently skipping if it already exists (SQLite-safe)."""
    try:
        op.add_column(table, sa.Column(column_name, column_type, nullable=True))
    except Exception:
        pass


def upgrade() -> None:
    # ---------------------------------------------------------------
    # activities - supplier data persistence
    # ---------------------------------------------------------------
    _add_column_if_not_exists("activities", "supplier_name", sa.String(255))
    _add_column_if_not_exists("activities", "supplier_ef", sa.Numeric())

    # ---------------------------------------------------------------
    # emissions - dual Scope 2 reporting
    # ---------------------------------------------------------------
    _add_column_if_not_exists("emissions", "location_co2e_kg", sa.Numeric())
    _add_column_if_not_exists("emissions", "market_co2e_kg", sa.Numeric())


def downgrade() -> None:
    op.drop_column("emissions", "market_co2e_kg")
    op.drop_column("emissions", "location_co2e_kg")
    op.drop_column("activities", "supplier_ef")
    op.drop_column("activities", "supplier_name")
