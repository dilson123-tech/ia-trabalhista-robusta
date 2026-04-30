"""add legal area and action type to cases

Revision ID: 5e57ae70ff0c
Revises: d8018dcce438
Create Date: 2026-04-29 23:55:07.328842

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e57ae70ff0c'
down_revision = 'd8018dcce438'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('cases', sa.Column('legal_area', sa.String(length=60), nullable=True))
    op.add_column('cases', sa.Column('action_type', sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column('cases', 'action_type')
    op.drop_column('cases', 'legal_area')
