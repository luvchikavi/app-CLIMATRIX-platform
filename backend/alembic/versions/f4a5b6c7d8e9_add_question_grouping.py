"""add grouping to clarification_questions (one question resolves many rows)

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-07-07 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clarification_questions",
        sa.Column("group_key", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "clarification_questions",
        sa.Column("applies_to_row_ids", sa.JSON(), nullable=True),
    )
    op.create_index(
        op.f("ix_clarification_questions_group_key"),
        "clarification_questions",
        ["group_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_clarification_questions_group_key"),
        table_name="clarification_questions",
    )
    op.drop_column("clarification_questions", "applies_to_row_ids")
    op.drop_column("clarification_questions", "group_key")
