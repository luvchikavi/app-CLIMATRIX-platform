"""add measurement_tier to staged_rows (the data-quality ladder)

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-07-07 10:00:00.000000

The spine of the parser: every staged line is placed on the ladder
measured | calculated | estimated | gap.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "staged_rows",
        sa.Column(
            "measurement_tier",
            sqlmodel.sql.sqltypes.AutoString(length=12),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_staged_rows_measurement_tier"),
        "staged_rows",
        ["measurement_tier"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_staged_rows_measurement_tier"), table_name="staged_rows")
    op.drop_column("staged_rows", "measurement_tier")
