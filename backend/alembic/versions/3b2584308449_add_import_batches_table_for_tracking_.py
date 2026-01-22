"""Add import_batches table for tracking uploads

Revision ID: 3b2584308449
Revises: 9f1327182331
Create Date: 2026-01-18 10:43:26.963718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3b2584308449'
down_revision: Union[str, None] = '9f1327182331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create import_batches table
    op.create_table(
        'import_batches',
        sa.Column('id', sa.CHAR(32), primary_key=True),
        sa.Column('organization_id', sa.CHAR(32), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('reporting_period_id', sa.CHAR(32), sa.ForeignKey('reporting_periods.id'), nullable=False, index=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('total_rows', sa.Integer, nullable=False, default=0),
        sa.Column('successful_rows', sa.Integer, nullable=False, default=0),
        sa.Column('failed_rows', sa.Integer, nullable=False, default=0),
        sa.Column('skipped_rows', sa.Integer, nullable=False, default=0),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('row_errors', sa.JSON, nullable=True),
        sa.Column('uploaded_by', sa.CHAR(32), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # Add foreign key from activities to import_batches
    # Note: SQLite doesn't support adding FK constraints to existing tables
    # For PostgreSQL (production), this will work
    op.create_index('ix_activities_import_batch_id', 'activities', ['import_batch_id'])


def downgrade() -> None:
    op.drop_index('ix_activities_import_batch_id', 'activities')
    op.drop_table('import_batches')
