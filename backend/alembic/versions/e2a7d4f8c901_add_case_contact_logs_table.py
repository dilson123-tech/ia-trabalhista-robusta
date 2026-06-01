"""add case contact logs table

Revision ID: e2a7d4f8c901
Revises: c9f7a4b2d601
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "e2a7d4f8c901"
down_revision = "c9f7a4b2d601"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_contact_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("contact_type", sa.String(length=40), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.String(length=240), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_contact_logs_tenant_id"), "case_contact_logs", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_case_contact_logs_case_id"), "case_contact_logs", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_contact_logs_case_id"), table_name="case_contact_logs")
    op.drop_index(op.f("ix_case_contact_logs_tenant_id"), table_name="case_contact_logs")
    op.drop_table("case_contact_logs")
