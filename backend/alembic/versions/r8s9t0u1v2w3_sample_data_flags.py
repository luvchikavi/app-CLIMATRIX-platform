"""Sample-data flags for the tool modules.

"Load sample data" now also seeds PCF products, an EPD project and CBAM
imports. Products already carry is_demo; footprints/BOM lines/EPDs derive
demo-ness from their product. SupplierPCF, CBAMImport and CBAMInstallation
are org-scoped with no product link, so they get their own flag.

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-07-22
"""

import sqlalchemy as sa
from alembic import op

revision = "r8s9t0u1v2w3"
down_revision = "q7r8s9t0u1v2"
branch_labels = None
depends_on = None

_TABLES = ["supplier_pcfs", "cbam_imports", "cbam_installations"]


def upgrade() -> None:
    for table in _TABLES:
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
    for table in _TABLES:
        op.drop_column(table, "is_demo")
