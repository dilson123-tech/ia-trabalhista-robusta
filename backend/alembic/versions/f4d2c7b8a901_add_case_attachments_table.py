"""add case attachments table

Revision ID: f4d2c7b8a901
Revises: 5e57ae70ff0c
Create Date: 2026-05-19 12:35:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f4d2c7b8a901"
down_revision = "5e57ae70ff0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=700), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="outro"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_path"),
        sa.UniqueConstraint("tenant_id", "case_id", "stored_filename", name="uq_case_attachments_tenant_case_file"),
    )
    op.create_index(op.f("ix_case_attachments_case_id"), "case_attachments", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_attachments_tenant_id"), "case_attachments", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_attachments_tenant_id"), table_name="case_attachments")
    op.drop_index(op.f("ix_case_attachments_case_id"), table_name="case_attachments")
    op.drop_table("case_attachments")
