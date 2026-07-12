"""CBAM certificate ledger

Adds cbam_certificate_entries: the definitive-regime certificate account
ledger (purchases from 1 Feb 2027, surrenders with the 30 Sep annual
declaration, Commission repurchases requested by 31 Oct). Source of truth
for the 50% quarterly holding check (Omnibus, Reg. (EU) 2025/2083).
`entry_type` is a plain varchar — no native PG enum, per the existing
prod rule.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cbam_certificate_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_eur", sa.Numeric(), nullable=True),
        sa.Column("total_eur", sa.Numeric(), nullable=True),
        sa.Column("declaration_year", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cbam_certificate_entries_organization_id",
        "cbam_certificate_entries",
        ["organization_id"],
    )
    op.create_index(
        "ix_cbam_certificate_entries_entry_date",
        "cbam_certificate_entries",
        ["entry_date"],
    )
    op.create_index(
        "ix_cbam_certificate_entries_declaration_year",
        "cbam_certificate_entries",
        ["declaration_year"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cbam_certificate_entries_declaration_year",
        table_name="cbam_certificate_entries",
    )
    op.drop_index(
        "ix_cbam_certificate_entries_entry_date",
        table_name="cbam_certificate_entries",
    )
    op.drop_index(
        "ix_cbam_certificate_entries_organization_id",
        table_name="cbam_certificate_entries",
    )
    op.drop_table("cbam_certificate_entries")
