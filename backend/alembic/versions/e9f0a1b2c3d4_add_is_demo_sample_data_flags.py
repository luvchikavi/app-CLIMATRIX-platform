"""Sample-data (is_demo) flags

Adds a boolean is_demo column to the five tables the "Load sample data"
button seeds (activities, sites, reporting_periods, decarbonization_targets,
scenarios), so DELETE /sample-data can remove exactly what the seed created
and the UI can badge those rows DEMO. Plain boolean with a false
server_default — deliberately NOT a new value on the native PG `datasource`
enum, per the existing prod rule.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None

TABLES = [
    "activities",
    "sites",
    "reporting_periods",
    "decarbonization_targets",
    "scenarios",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "is_demo",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "is_demo")
