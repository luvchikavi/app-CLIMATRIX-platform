"""CBAM supplier portal: data requests + supplier emission rows

Adds the Phase 3 supplier portal tables:

- cbam_data_requests: tokenized magic-link requests an EU importer sends to
  a non-EU installation operator (supplier) asking for actual embedded
  emissions. `status` is a plain varchar (pending/submitted/expired) — no
  native PG enum, per the existing prod rule.
- cbam_supplier_emissions: the per-CN-code SEE rows the supplier submits
  via the public form. Separate table (not JSON) so the annual declaration
  can match rows by installation + CN-code prefix.

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-07-09
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cbam_data_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("installation_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_email", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("requested_by", sa.Uuid(), nullable=True),
        sa.Column("message", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["installation_id"], ["cbam_installations.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cbam_data_requests_organization_id",
        "cbam_data_requests",
        ["organization_id"],
    )
    op.create_index(
        "ix_cbam_data_requests_installation_id",
        "cbam_data_requests",
        ["installation_id"],
    )
    op.create_index(
        "ix_cbam_data_requests_token", "cbam_data_requests", ["token"], unique=True
    )

    op.create_table(
        "cbam_supplier_emissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("installation_id", sa.Uuid(), nullable=False),
        sa.Column("cn_code", sa.String(length=10), nullable=False),
        sa.Column("direct_see_tco2e_per_t", sa.Numeric(), nullable=False),
        sa.Column("indirect_see_tco2e_per_t", sa.Numeric(), nullable=True),
        sa.Column("production_period_start", sa.Date(), nullable=False),
        sa.Column("production_period_end", sa.Date(), nullable=False),
        sa.Column("verifier_name", sa.String(length=255), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["cbam_data_requests.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["installation_id"], ["cbam_installations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cbam_supplier_emissions_request_id",
        "cbam_supplier_emissions",
        ["request_id"],
    )
    op.create_index(
        "ix_cbam_supplier_emissions_organization_id",
        "cbam_supplier_emissions",
        ["organization_id"],
    )
    op.create_index(
        "ix_cbam_supplier_emissions_installation_id",
        "cbam_supplier_emissions",
        ["installation_id"],
    )
    op.create_index(
        "ix_cbam_supplier_emissions_cn_code",
        "cbam_supplier_emissions",
        ["cn_code"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cbam_supplier_emissions_cn_code", table_name="cbam_supplier_emissions"
    )
    op.drop_index(
        "ix_cbam_supplier_emissions_installation_id",
        table_name="cbam_supplier_emissions",
    )
    op.drop_index(
        "ix_cbam_supplier_emissions_organization_id",
        table_name="cbam_supplier_emissions",
    )
    op.drop_index(
        "ix_cbam_supplier_emissions_request_id", table_name="cbam_supplier_emissions"
    )
    op.drop_table("cbam_supplier_emissions")
    op.drop_index("ix_cbam_data_requests_token", table_name="cbam_data_requests")
    op.drop_index(
        "ix_cbam_data_requests_installation_id", table_name="cbam_data_requests"
    )
    op.drop_index(
        "ix_cbam_data_requests_organization_id", table_name="cbam_data_requests"
    )
    op.drop_table("cbam_data_requests")
