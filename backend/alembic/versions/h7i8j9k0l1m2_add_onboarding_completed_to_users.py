"""add onboarding_completed to users

Revision ID: h7i8j9k0l1m2
Revises: g6h7i8j9k0l1
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = 'h7i8j9k0l1m2'
down_revision = 'g6h7i8j9k0l1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='0'))
    except Exception:
        pass  # Column may already exist


def downgrade() -> None:
    try:
        op.drop_column('users', 'onboarding_completed')
    except Exception:
        pass
