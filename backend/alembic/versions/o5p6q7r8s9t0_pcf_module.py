"""PCF module — products, BOM inputs, supplier PCFs, footprint snapshots.

ISO 14067 / PACT Methodology v3 product carbon footprints: Product (declared
unit + CN-code CBAM link), ProductInput (BOM lines grounded in the factor
library or a supplier PCF, EN 15804 module-tagged for the LCA-lite phase),
SupplierPCF (PACT exchange ingests), ProductFootprint (immutable-once-final
computed snapshots with full per-line provenance).

Statuses are varchar, not native PG enums (platform convention).

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "o5p6q7r8s9t0"
down_revision = "n4o5p6q7r8s9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("declared_unit", sa.String(length=30), nullable=False),
        sa.Column("declared_unit_amount", sa.Numeric(), nullable=False),
        sa.Column("cn_code", sa.String(length=10), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_organization_id", "products", ["organization_id"])
    op.create_index("ix_products_cn_code", "products", ["cn_code"])

    op.create_table(
        "supplier_pcfs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_name", sa.String(length=255), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("pcf_value", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("boundary", sa.String(length=30), nullable=False),
        sa.Column("primary_data_share", sa.Float(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("pact_pf_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_supplier_pcfs_organization_id", "supplier_pcfs", ["organization_id"]
    )

    op.create_table(
        "product_inputs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("input_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity_per_unit", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("activity_key", sa.String(length=100), nullable=True),
        sa.Column("supplier_pcf_id", sa.Uuid(), nullable=True),
        sa.Column("category_code", sa.String(length=10), nullable=True),
        sa.Column("scope", sa.Integer(), nullable=True),
        sa.Column("region", sa.String(length=50), nullable=True),
        sa.Column("en15804_module", sa.String(length=5), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["supplier_pcf_id"], ["supplier_pcfs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_inputs_organization_id", "product_inputs", ["organization_id"]
    )
    op.create_index("ix_product_inputs_product_id", "product_inputs", ["product_id"])
    op.create_index(
        "ix_product_inputs_activity_key", "product_inputs", ["activity_key"]
    )

    op.create_table(
        "product_footprints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("reporting_period_id", sa.Uuid(), nullable=False),
        sa.Column("declared_unit", sa.String(length=30), nullable=False),
        sa.Column("declared_unit_amount", sa.Numeric(), nullable=False),
        sa.Column("boundary", sa.String(length=30), nullable=False),
        sa.Column("total_kgco2e_per_unit", sa.Numeric(), nullable=False),
        sa.Column("fossil_kgco2e_per_unit", sa.Numeric(), nullable=True),
        sa.Column("biogenic_kgco2e_per_unit", sa.Numeric(), nullable=True),
        sa.Column("primary_data_share", sa.Float(), nullable=True),
        sa.Column("stage_breakdown", sa.JSON(), nullable=True),
        sa.Column("line_items", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
        sa.Column("methodology", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["reporting_period_id"], ["reporting_periods.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_footprints_organization_id",
        "product_footprints",
        ["organization_id"],
    )
    op.create_index(
        "ix_product_footprints_product_id", "product_footprints", ["product_id"]
    )
    op.create_index(
        "ix_product_footprints_reporting_period_id",
        "product_footprints",
        ["reporting_period_id"],
    )


def downgrade() -> None:
    op.drop_table("product_footprints")
    op.drop_table("product_inputs")
    op.drop_table("supplier_pcfs")
    op.drop_table("products")
