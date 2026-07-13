"""CBAM default values: per-country + dataset version columns, representative seed

Adds `country_code` (origin country, NULL = any), `dataset_year` and
`dataset_version` to cbam_default_values so the table can hold the
Commission's definitive-period default values (per CN code x origin
country, published 13 Feb 2026) alongside versioned updates.

Also seeds the representative per-sector values used by the screening
service (source='representative_v0') so the DB path works before the
official Commission file is loaded via
`python -m app.cli.seed load-cbam-defaults <file>`.

The new columns are plain String (no native PG enums), per the rule for
migration-created columns. The pre-existing `sector` column, however, IS
the native PG enum `cbamsector` in production (the table there predates
the migration chain and was created from model metadata), while chain-built
databases have VARCHAR(20) — the seed below handles both.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-07-09
"""

import uuid
from datetime import date

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


# Representative per-sector default intensities (tCO2e/t; electricity is
# tCO2e/MWh), mirrored from app/services/cbam_screening.py. One row per
# Annex I CN prefix; country_code NULL = country-independent fallback.
_REPRESENTATIVE_ROWS = [
    # (cn_code_prefix, sector, description, total_see)
    ("2523", "cement", "Cement (representative)", "0.95"),
    ("72", "iron_steel", "Iron & steel (representative)", "2.5"),
    ("73", "iron_steel", "Articles of iron or steel (representative)", "2.5"),
    ("76", "aluminium", "Aluminium (representative)", "8.0"),
    ("2808", "fertiliser", "Nitric acid (representative)", "2.5"),
    ("2814", "fertiliser", "Ammonia (representative)", "2.5"),
    ("283421", "fertiliser", "Nitrates of potassium (representative)", "2.5"),
    ("3102", "fertiliser", "Mineral nitrogen fertilisers (representative)", "2.5"),
    ("3105", "fertiliser", "Mixed fertilisers (representative)", "2.5"),
    ("2804", "hydrogen", "Hydrogen (representative)", "12.0"),
    ("2716", "electricity", "Electricity, tCO2e/MWh (representative)", "0.75"),
]


def upgrade() -> None:
    op.add_column(
        "cbam_default_values",
        sa.Column("country_code", sa.String(2), nullable=True),
    )
    op.add_column(
        "cbam_default_values",
        sa.Column("dataset_year", sa.Integer(), nullable=True),
    )
    op.add_column(
        "cbam_default_values",
        sa.Column("dataset_version", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_cbam_default_values_country_code",
        "cbam_default_values",
        ["country_code"],
    )
    op.create_index(
        "ix_cbam_default_values_dataset_year",
        "cbam_default_values",
        ["dataset_year"],
    )

    # Seed representative sector-level values (idempotent enough: this
    # migration only runs once; the CLI seeder skips existing rows).
    #
    # `sector` storage differs by environment: chain-built databases have
    # VARCHAR(20), but production's column is the native PG enum
    # `cbamsector` whose labels are the CBAMSector member NAMES
    # ('CEMENT', ...). The ORM's sa.Enum writes and reads those names on
    # both storages, so the seed always inserts names; the ad-hoc column
    # type below only controls the bind cast the driver emits.
    bind = op.get_bind()
    sector_type: sa.types.TypeEngine = sa.String()
    if bind.dialect.name == "postgresql":
        udt = bind.execute(
            sa.text(
                "SELECT udt_name FROM information_schema.columns "
                "WHERE table_name = 'cbam_default_values' "
                "AND column_name = 'sector'"
            )
        ).scalar()
        if udt == "cbamsector":
            sector_type = postgresql.ENUM(name="cbamsector", create_type=False)
            # The model's CBAMSector gained OTHER after production's type
            # was created; add the label so ORM writes of CBAMSector.OTHER
            # can't fail. Safe inside this transaction on PG 12+ because
            # the new label is not used before commit.
            op.execute(sa.text("ALTER TYPE cbamsector ADD VALUE IF NOT EXISTS 'OTHER'"))
    table = sa.table(
        "cbam_default_values",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("cn_code", sa.String),
        sa.column("sector", sector_type),
        sa.column("product_description", sa.String),
        sa.column("country_code", sa.String),
        sa.column("dataset_year", sa.Integer),
        sa.column("dataset_version", sa.String),
        sa.column("direct_see", sa.Numeric),
        sa.column("indirect_see", sa.Numeric),
        sa.column("total_see", sa.Numeric),
        sa.column("source", sa.String),
        sa.column("source_reference", sa.String),
        sa.column("valid_from", sa.Date),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        table,
        [
            {
                "id": uuid.uuid4(),
                "cn_code": cn,
                # Member NAME (e.g. 'IRON_STEEL') — what sa.Enum stores.
                "sector": sector.upper(),
                "product_description": desc,
                "country_code": None,
                "dataset_year": 2026,
                "dataset_version": "representative_v0",
                # Representative values are totals; the direct/indirect
                # split is unknown at sector level.
                "direct_see": see,
                "indirect_see": None,
                "total_see": see,
                "source": "representative_v0",
                "source_reference": "app/services/cbam_screening.py",
                "valid_from": date(2026, 1, 1),
                "is_active": True,
            }
            for cn, sector, desc, see in _REPRESENTATIVE_ROWS
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM cbam_default_values WHERE source = 'representative_v0'")
    op.drop_index(
        "ix_cbam_default_values_dataset_year", table_name="cbam_default_values"
    )
    op.drop_index(
        "ix_cbam_default_values_country_code", table_name="cbam_default_values"
    )
    op.drop_column("cbam_default_values", "dataset_version")
    op.drop_column("cbam_default_values", "dataset_year")
    op.drop_column("cbam_default_values", "country_code")
