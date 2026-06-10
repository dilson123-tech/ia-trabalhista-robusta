"""add case timeline items

Revision ID: a4b9c6d7e810
Revises: f19c0e1a2b33
Create Date: 2026-06-09 10:36:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a4b9c6d7e810"
down_revision = "f19c0e1a2b33"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_timeline_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.String(length=80), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("related_evidence", sa.Text(), nullable=True),
        sa.Column("related_witness", sa.String(length=240), nullable=True),
        sa.Column("pending_note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeline_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_timeline_items_tenant_id",
        "case_timeline_items",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_timeline_items_case_id",
        "case_timeline_items",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_timeline_items_case_order",
        "case_timeline_items",
        ["case_id", "sort_order", "id"],
        unique=False,
    )
    op.create_index(
        "ix_case_timeline_items_case_created_at",
        "case_timeline_items",
        ["case_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_case_timeline_items_case_created_at", table_name="case_timeline_items")
    op.drop_index("ix_case_timeline_items_case_order", table_name="case_timeline_items")
    op.drop_index("ix_case_timeline_items_case_id", table_name="case_timeline_items")
    op.drop_index("ix_case_timeline_items_tenant_id", table_name="case_timeline_items")
    op.drop_table("case_timeline_items")
