"""Add verification workflow fields to reporting_periods

Revision ID: a1b2c3d4e5f6
Revises: 596f18c9a233
Create Date: 2026-01-25

Adds fields for the GHG inventory verification workflow:
- status: Workflow state (draft, review, submitted, audit, verified, locked)
- assurance_level: Type of assurance (limited, reasonable)
- submitted_at, submitted_by_id: Track who submitted and when
- verified_at, verified_by: Track verification details
- verification_statement: Auditor's statement
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '596f18c9a233'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification workflow columns to reporting_periods table
    op.add_column('reporting_periods', sa.Column('status', sa.String(20), nullable=False, server_default='draft'))
    op.add_column('reporting_periods', sa.Column('assurance_level', sa.String(20), nullable=True))
    op.add_column('reporting_periods', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    op.add_column('reporting_periods', sa.Column('submitted_by_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.add_column('reporting_periods', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('reporting_periods', sa.Column('verified_by', sa.String(255), nullable=True))
    op.add_column('reporting_periods', sa.Column('verification_statement', sa.Text(), nullable=True))

    # Add foreign key for submitted_by_id
    op.create_foreign_key(
        'fk_reporting_periods_submitted_by',
        'reporting_periods', 'users',
        ['submitted_by_id'], ['id']
    )


def downgrade() -> None:
    # Remove foreign key first
    op.drop_constraint('fk_reporting_periods_submitted_by', 'reporting_periods', type_='foreignkey')

    # Remove columns
    op.drop_column('reporting_periods', 'verification_statement')
    op.drop_column('reporting_periods', 'verified_by')
    op.drop_column('reporting_periods', 'verified_at')
    op.drop_column('reporting_periods', 'submitted_by_id')
    op.drop_column('reporting_periods', 'submitted_at')
    op.drop_column('reporting_periods', 'assurance_level')
    op.drop_column('reporting_periods', 'status')
