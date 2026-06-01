"""add client whatsapp fields to cases

Revision ID: c9f7a4b2d601
Revises: f4d2c7b8a901
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "c9f7a4b2d601"
down_revision = "f4d2c7b8a901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("client_name", sa.String(length=160), nullable=True))
    op.add_column("cases", sa.Column("client_whatsapp", sa.String(length=32), nullable=True))
    op.add_column(
        "cases",
        sa.Column(
            "client_whatsapp_consent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "cases",
        sa.Column("client_whatsapp_consent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "client_whatsapp_consent_at")
    op.drop_column("cases", "client_whatsapp_consent")
    op.drop_column("cases", "client_whatsapp")
    op.drop_column("cases", "client_name")
