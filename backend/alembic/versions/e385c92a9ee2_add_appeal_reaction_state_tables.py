"""add appeal reaction state tables

Revision ID: e385c92a9ee2
Revises: 7ca5cfb92bc1
Create Date: 2026-03-20 12:24:51.753262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e385c92a9ee2"
down_revision = "7ca5cfb92bc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appeal_reaction_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("area", sa.String(length=50), nullable=False),
        sa.Column("decision_type", sa.String(length=50), nullable=False),
        sa.Column("decision_title", sa.String(length=255), nullable=False),
        sa.Column("decision_summary", sa.Text(), nullable=True),
        sa.Column("decision_date", sa.String(length=50), nullable=True),
        sa.Column("decision_metadata", sa.JSON(), nullable=False),
        sa.Column("state_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appeal_reaction_states_case_decision_date",
        "appeal_reaction_states",
        ["case_id", "decision_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appeal_reaction_states_case_id"),
        "appeal_reaction_states",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_appeal_reaction_states_case_id_updated_at",
        "appeal_reaction_states",
        ["case_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appeal_reaction_states_tenant_id"),
        "appeal_reaction_states",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "appeal_deadlines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("appeal_reaction_state_id", sa.Integer(), nullable=False),
        sa.Column("deadline_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("due_date", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("deadline_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appeal_reaction_state_id"],
            ["appeal_reaction_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "appeal_reaction_state_id",
            "deadline_key",
            name="uq_appeal_deadlines_tenant_state_deadline_key",
        ),
    )
    op.create_index(
        op.f("ix_appeal_deadlines_appeal_reaction_state_id"),
        "appeal_deadlines",
        ["appeal_reaction_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_appeal_deadlines_state_status",
        "appeal_deadlines",
        ["appeal_reaction_state_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appeal_deadlines_tenant_id"),
        "appeal_deadlines",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "appeal_decision_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("appeal_reaction_state_id", sa.Integer(), nullable=False),
        sa.Column("point_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("legal_effect", sa.String(length=255), nullable=True),
        sa.Column("point_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appeal_reaction_state_id"],
            ["appeal_reaction_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "appeal_reaction_state_id",
            "point_key",
            name="uq_appeal_decision_points_tenant_state_point_key",
        ),
    )
    op.create_index(
        op.f("ix_appeal_decision_points_appeal_reaction_state_id"),
        "appeal_decision_points",
        ["appeal_reaction_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_appeal_decision_points_state_outcome",
        "appeal_decision_points",
        ["appeal_reaction_state_id", "outcome"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appeal_decision_points_tenant_id"),
        "appeal_decision_points",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "appeal_draft_refs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("appeal_reaction_state_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("draft_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appeal_reaction_state_id"],
            ["appeal_reaction_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_appeal_draft_refs_appeal_reaction_state_id"),
        "appeal_draft_refs",
        ["appeal_reaction_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_appeal_draft_refs_state_status",
        "appeal_draft_refs",
        ["appeal_reaction_state_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appeal_draft_refs_tenant_id"),
        "appeal_draft_refs",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "appeal_strategy_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("appeal_reaction_state_id", sa.Integer(), nullable=False),
        sa.Column("strategy_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_point_keys", sa.JSON(), nullable=False),
        sa.Column("priority", sa.String(length=30), nullable=False),
        sa.Column("strategy_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appeal_reaction_state_id"],
            ["appeal_reaction_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "appeal_reaction_state_id",
            "strategy_key",
            name="uq_appeal_strategy_items_tenant_state_strategy_key",
        ),
    )
    op.create_index(
        op.f("ix_appeal_strategy_items_appeal_reaction_state_id"),
        "appeal_strategy_items",
        ["appeal_reaction_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_appeal_strategy_items_state_priority",
        "appeal_strategy_items",
        ["appeal_reaction_state_id", "priority"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appeal_strategy_items_tenant_id"),
        "appeal_strategy_items",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_appeal_strategy_items_tenant_id"),
        table_name="appeal_strategy_items",
    )
    op.drop_index(
        "ix_appeal_strategy_items_state_priority",
        table_name="appeal_strategy_items",
    )
    op.drop_index(
        op.f("ix_appeal_strategy_items_appeal_reaction_state_id"),
        table_name="appeal_strategy_items",
    )
    op.drop_table("appeal_strategy_items")

    op.drop_index(
        op.f("ix_appeal_draft_refs_tenant_id"),
        table_name="appeal_draft_refs",
    )
    op.drop_index(
        "ix_appeal_draft_refs_state_status",
        table_name="appeal_draft_refs",
    )
    op.drop_index(
        op.f("ix_appeal_draft_refs_appeal_reaction_state_id"),
        table_name="appeal_draft_refs",
    )
    op.drop_table("appeal_draft_refs")

    op.drop_index(
        op.f("ix_appeal_decision_points_tenant_id"),
        table_name="appeal_decision_points",
    )
    op.drop_index(
        "ix_appeal_decision_points_state_outcome",
        table_name="appeal_decision_points",
    )
    op.drop_index(
        op.f("ix_appeal_decision_points_appeal_reaction_state_id"),
        table_name="appeal_decision_points",
    )
    op.drop_table("appeal_decision_points")

    op.drop_index(
        op.f("ix_appeal_deadlines_tenant_id"),
        table_name="appeal_deadlines",
    )
    op.drop_index(
        "ix_appeal_deadlines_state_status",
        table_name="appeal_deadlines",
    )
    op.drop_index(
        op.f("ix_appeal_deadlines_appeal_reaction_state_id"),
        table_name="appeal_deadlines",
    )
    op.drop_table("appeal_deadlines")

    op.drop_index(
        op.f("ix_appeal_reaction_states_tenant_id"),
        table_name="appeal_reaction_states",
    )
    op.drop_index(
        "ix_appeal_reaction_states_case_id_updated_at",
        table_name="appeal_reaction_states",
    )
    op.drop_index(
        op.f("ix_appeal_reaction_states_case_id"),
        table_name="appeal_reaction_states",
    )
    op.drop_index(
        "ix_appeal_reaction_states_case_decision_date",
        table_name="appeal_reaction_states",
    )
    op.drop_table("appeal_reaction_states")
