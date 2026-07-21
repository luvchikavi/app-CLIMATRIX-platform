"""EPD generator — epd_projects table + EPD scope on verifier_access.

EPDProject: an EN 15804+A2 declaration in preparation, pinned to a
finalized ProductFootprint; results (PCF totals + LCA matrix) freeze as a
JSON copy when the project leaves draft. Status machine draft →
internal_review → verification → registered → published | expired,
5-year validity.

verifier_access grows a second (mutually exclusive) scope: epd_project_id —
the "reuse VerifierAccess" parameter change from the module design doc.
reporting_period_id becomes nullable to allow EPD-only grants.

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "q7r8s9t0u1v2"
down_revision = "p6q7r8s9t0u1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "epd_projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("footprint_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("pcr", sa.String(length=100), nullable=False),
        sa.Column("program_operator", sa.String(length=255), nullable=True),
        sa.Column("declared_unit", sa.String(length=30), nullable=False),
        sa.Column("declared_unit_amount", sa.Numeric(), nullable=False),
        sa.Column("functional_unit", sa.String(length=255), nullable=True),
        sa.Column("rsl_years", sa.Integer(), nullable=True),
        sa.Column("scope_modules", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("results_frozen_at", sa.DateTime(), nullable=True),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("verifier_statement", sa.String(length=2000), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["footprint_id"], ["product_footprints.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_epd_projects_organization_id", "epd_projects", ["organization_id"]
    )
    op.create_index("ix_epd_projects_product_id", "epd_projects", ["product_id"])

    op.add_column(
        "verifier_access", sa.Column("epd_project_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_verifier_access_epd_project_id",
        "verifier_access",
        "epd_projects",
        ["epd_project_id"],
        ["id"],
    )
    op.create_index(
        "ix_verifier_access_epd_project_id", "verifier_access", ["epd_project_id"]
    )
    op.alter_column(
        "verifier_access",
        "reporting_period_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "verifier_access",
        "reporting_period_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.drop_index("ix_verifier_access_epd_project_id", table_name="verifier_access")
    op.drop_constraint(
        "fk_verifier_access_epd_project_id", "verifier_access", type_="foreignkey"
    )
    op.drop_column("verifier_access", "epd_project_id")
    op.drop_index("ix_epd_projects_product_id", table_name="epd_projects")
    op.drop_index("ix_epd_projects_organization_id", table_name="epd_projects")
    op.drop_table("epd_projects")
