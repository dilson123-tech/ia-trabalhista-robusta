"""add case evidence checklist items

Revision ID: f19c0e1a2b33
Revises: e2a7d4f8c901
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa


revision = "f19c0e1a2b33"
down_revision = "e2a7d4f8c901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_evidence_checklist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("attachment_id", sa.Integer(), nullable=True),
        sa.Column("item_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="outro"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("requested_from", sa.String(length=160), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("checklist_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["attachment_id"], ["case_attachments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "case_id",
            "item_key",
            name="uq_case_evidence_checklist_tenant_case_key",
        ),
    )
    op.create_index(
        op.f("ix_case_evidence_checklist_items_tenant_id"),
        "case_evidence_checklist_items",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_evidence_checklist_items_case_id"),
        "case_evidence_checklist_items",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_evidence_checklist_items_attachment_id"),
        "case_evidence_checklist_items",
        ["attachment_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_evidence_checklist_case_status",
        "case_evidence_checklist_items",
        ["case_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_case_evidence_checklist_case_priority",
        "case_evidence_checklist_items",
        ["case_id", "priority"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_case_evidence_checklist_case_priority", table_name="case_evidence_checklist_items")
    op.drop_index("ix_case_evidence_checklist_case_status", table_name="case_evidence_checklist_items")
    op.drop_index(op.f("ix_case_evidence_checklist_items_attachment_id"), table_name="case_evidence_checklist_items")
    op.drop_index(op.f("ix_case_evidence_checklist_items_case_id"), table_name="case_evidence_checklist_items")
    op.drop_index(op.f("ix_case_evidence_checklist_items_tenant_id"), table_name="case_evidence_checklist_items")
    op.drop_table("case_evidence_checklist_items")
