"""Biogenic CO2 tracking (reported separately, outside the scopes)

Adds emission_factors.biogenic_co2_factor (biogenic CO2 per activity unit,
DEFRA "outside of scopes") and emissions.biogenic_co2_kg (the calculated
per-activity biogenic total). Both nullable — only biofuel/biomass factors
carry a value, and existing rows are untouched. This lets the ISO 14064
report state "biogenic reported separately" truthfully instead of claiming
a disclosure the system never computed.

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f0a1b2c3d4e5"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "emission_factors",
        sa.Column("biogenic_co2_factor", sa.Numeric(), nullable=True),
    )
    op.add_column(
        "emissions",
        sa.Column("biogenic_co2_kg", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("emissions", "biogenic_co2_kg")
    op.drop_column("emission_factors", "biogenic_co2_factor")
