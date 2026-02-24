"""add power_producers table for market-based scope 2

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'power_producers',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('producer_name_he', sa.String(length=255), nullable=True),
        sa.Column('producer_name_en', sa.String(length=255), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('co2e_per_kwh', sa.Numeric(), nullable=False),
        sa.Column('co2_per_kwh', sa.Numeric(), nullable=True),
        sa.Column('ch4_per_kwh', sa.Numeric(), nullable=True),
        sa.Column('n2o_per_kwh', sa.Numeric(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='residual_mix'),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_power_producers_country_code', 'power_producers', ['country_code'])
    op.create_index('ix_power_producers_year', 'power_producers', ['year'])


def downgrade() -> None:
    op.drop_index('ix_power_producers_year', 'power_producers')
    op.drop_index('ix_power_producers_country_code', 'power_producers')
    op.drop_table('power_producers')
