"""LCA-lite — impact_factors table + frozen LCA matrix on footprints.

ImpactFactor: EF 3.1 multi-indicator reference rows (dataset × indicator ×
region), the LCIA sibling of emission_factors; curated data seeds/syncs at
startup. product_footprints.lca_results: the EF 3.1 indicator × EN 15804
module matrix frozen per snapshot (what a future EPD version pins to).

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "p6q7r8s9t0u1"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "impact_factors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_key", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=50), nullable=False),
        sa.Column("indicator_code", sa.String(length=50), nullable=False),
        # Explicit scale — LCIA values reach e-13; see ImpactFactor model note.
        sa.Column("value", sa.Numeric(38, 24), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("activity_unit", sa.String(length=50), nullable=False),
        sa.Column("method_version", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_impact_factors_dataset_key", "impact_factors", ["dataset_key"])
    op.create_index("ix_impact_factors_region", "impact_factors", ["region"])
    op.create_index(
        "ix_impact_factors_indicator_code", "impact_factors", ["indicator_code"]
    )
    op.create_index(
        "ix_impact_factors_method_version", "impact_factors", ["method_version"]
    )
    op.create_index("ix_impact_factors_year", "impact_factors", ["year"])

    op.add_column(
        "product_footprints", sa.Column("lca_results", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("product_footprints", "lca_results")
    op.drop_table("impact_factors")
