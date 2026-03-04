"""add users.is_active

Revision ID: a964c9bcfb2d
Revises: 0786ce015a07
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa


revision = 'a964c9bcfb2d'
down_revision = '0786ce015a07'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true()
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'is_active')
