"""add data-hub inventory profile (org fields + category_profiles + question category)

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-07-07 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Layer-0 profile facts on the organization
    op.add_column(
        "organizations", sa.Column("currency", sa.String(length=3), nullable=True)
    )
    op.add_column(
        "organizations",
        sa.Column(
            "unit_system",
            sa.String(length=10),
            nullable=False,
            server_default="metric",
        ),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "consolidation_approach",
            sa.String(length=30),
            nullable=False,
            server_default="operational_control",
        ),
    )

    # The standing per-category profile (relevance stored as varchar, not a
    # native PG enum — see the ingestion status precedent)
    op.create_table(
        "category_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=True),
        sa.Column("scope", sa.Integer(), nullable=False),
        sa.Column("category_code", sa.String(length=10), nullable=False),
        sa.Column("relevance", sa.String(length=20), nullable=False),
        sa.Column("exclusion_reason", sa.String(length=500), nullable=True),
        sa.Column("calculate_this_period", sa.Boolean(), nullable=False),
        sa.Column("data_owner", sa.String(length=255), nullable=True),
        sa.Column("expected_form", sa.String(length=20), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_category_profiles_organization_id"),
        "category_profiles",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_category_profiles_site_id"),
        "category_profiles",
        ["site_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_category_profiles_category_code"),
        "category_profiles",
        ["category_code"],
        unique=False,
    )

    # Pool open questions per category in the hub
    op.add_column(
        "clarification_questions",
        sa.Column("category_code", sa.String(length=10), nullable=True),
    )
    op.create_index(
        op.f("ix_clarification_questions_category_code"),
        "clarification_questions",
        ["category_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_clarification_questions_category_code"),
        table_name="clarification_questions",
    )
    op.drop_column("clarification_questions", "category_code")
    op.drop_index(
        op.f("ix_category_profiles_category_code"), table_name="category_profiles"
    )
    op.drop_index(op.f("ix_category_profiles_site_id"), table_name="category_profiles")
    op.drop_index(
        op.f("ix_category_profiles_organization_id"), table_name="category_profiles"
    )
    op.drop_table("category_profiles")
    op.drop_column("organizations", "consolidation_approach")
    op.drop_column("organizations", "unit_system")
    op.drop_column("organizations", "currency")
