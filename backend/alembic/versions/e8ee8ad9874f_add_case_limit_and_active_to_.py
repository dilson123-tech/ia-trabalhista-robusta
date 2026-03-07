"""add case_limit and active to subscriptions

Revision ID: e8ee8ad9874f
Revises: a964c9bcfb2d
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e8ee8ad9874f"
down_revision = "a964c9bcfb2d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("case_limit", sa.Integer(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("active", sa.Boolean(), nullable=True),
    )

    op.execute("UPDATE subscriptions SET case_limit = 10 WHERE case_limit IS NULL")
    op.execute("UPDATE subscriptions SET active = TRUE WHERE active IS NULL")

    op.alter_column("subscriptions", "case_limit", nullable=False)
    op.alter_column("subscriptions", "active", nullable=False)


def downgrade() -> None:
    op.drop_column("subscriptions", "active")
    op.drop_column("subscriptions", "case_limit")
