"""Add data quality fields to activities

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-25

Adds PCAF-style data quality scoring fields:
- data_quality_score: 1-5 scale (1=best, 5=worst)
- data_quality_justification: Optional explanation
- supporting_document_url: Link to evidence/documentation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add data quality columns to activities table
    op.add_column('activities', sa.Column('data_quality_score', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('activities', sa.Column('data_quality_justification', sa.String(500), nullable=True))
    op.add_column('activities', sa.Column('supporting_document_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'supporting_document_url')
    op.drop_column('activities', 'data_quality_justification')
    op.drop_column('activities', 'data_quality_score')
