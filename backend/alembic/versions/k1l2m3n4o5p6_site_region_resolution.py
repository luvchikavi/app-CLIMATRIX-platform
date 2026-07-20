"""Per-site factor regions — activities.region + ingestion_sessions.site_id.

Multi-country orgs were getting the org default_region's grid factor for
EVERY site. Two columns make site-aware resolution stick:

- activities.region: the row-level factor-region context (a derived hotel
  row's stay country, or the site's grid_region at commit), so recalculation
  re-resolves with the SAME region instead of flattening back to the org
  default.
- ingestion_sessions.site_id: which site a Smart-Import upload belongs to,
  chosen at upload; grounding + commit resolve factors in that site's region
  and committed activities carry the site.

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activities",
        sa.Column("region", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "ingestion_sessions",
        sa.Column("site_id", sa.Uuid(), nullable=True),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # SQLite (dev/tests) gets its schema from create_all; the FK + index
        # only need to exist on Postgres. ON DELETE SET NULL matches the
        # ingestion-chain rule from j0k1l2m3n4o5: deleting a Site must not
        # 500 on historical upload sessions.
        op.create_foreign_key(
            "ingestion_sessions_site_id_fkey",
            "ingestion_sessions",
            "sites",
            ["site_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_ingestion_sessions_site_id", "ingestion_sessions", ["site_id"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_ingestion_sessions_site_id", table_name="ingestion_sessions")
        op.drop_constraint(
            "ingestion_sessions_site_id_fkey", "ingestion_sessions", type_="foreignkey"
        )
    op.drop_column("ingestion_sessions", "site_id")
    op.drop_column("activities", "region")
