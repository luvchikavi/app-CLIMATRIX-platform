"""add calculation metadata columns to emissions table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('emissions', sa.Column('factor_year', sa.Integer(), nullable=True))
    op.add_column('emissions', sa.Column('factor_region', sa.String(length=50), nullable=True))
    op.add_column('emissions', sa.Column('method_hierarchy', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('emissions', 'method_hierarchy')
    op.drop_column('emissions', 'factor_region')
    op.drop_column('emissions', 'factor_year')
