"""add editable documents tables

Revision ID: b3f8b3e51eb3
Revises: 0786ce015a07
Create Date: 2026-03-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3f8b3e51eb3"
down_revision = "e8ee8ad9874f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "editable_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("area", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("current_version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("document_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_editable_documents_tenant_id",
        "editable_documents",
        ["tenant_id"],
    )
    op.create_index(
        "ix_editable_documents_case_id",
        "editable_documents",
        ["case_id"],
    )
    op.create_index(
        "ix_editable_documents_created_by_user_id",
        "editable_documents",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_editable_documents_case_id_updated_at",
        "editable_documents",
        ["case_id", "updated_at"],
    )

    op.create_table(
        "editable_document_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("editable_document_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("version_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["editable_document_id"],
            ["editable_documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "tenant_id",
            "editable_document_id",
            "version_number",
            name="uq_editable_document_versions_tenant_doc_version",
        ),
    )
    op.create_index(
        "ix_editable_document_versions_tenant_id",
        "editable_document_versions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_editable_document_versions_editable_document_id",
        "editable_document_versions",
        ["editable_document_id"],
    )
    op.create_index(
        "ix_editable_document_versions_created_by_user_id",
        "editable_document_versions",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_editable_document_versions_doc_created_at",
        "editable_document_versions",
        ["editable_document_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_editable_document_versions_doc_created_at",
        table_name="editable_document_versions",
    )
    op.drop_index(
        "ix_editable_document_versions_created_by_user_id",
        table_name="editable_document_versions",
    )
    op.drop_index(
        "ix_editable_document_versions_editable_document_id",
        table_name="editable_document_versions",
    )
    op.drop_index(
        "ix_editable_document_versions_tenant_id",
        table_name="editable_document_versions",
    )
    op.drop_table("editable_document_versions")

    op.drop_index(
        "ix_editable_documents_case_id_updated_at",
        table_name="editable_documents",
    )
    op.drop_index(
        "ix_editable_documents_created_by_user_id",
        table_name="editable_documents",
    )
    op.drop_index(
        "ix_editable_documents_case_id",
        table_name="editable_documents",
    )
    op.drop_index(
        "ix_editable_documents_tenant_id",
        table_name="editable_documents",
    )
    op.drop_table("editable_documents")
