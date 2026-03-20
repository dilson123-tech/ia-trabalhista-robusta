"""add case party state tables

Revision ID: 7ca5cfb92bc1
Revises: b3f8b3e51eb3
Create Date: 2026-03-20 07:33:16.957318

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7ca5cfb92bc1"
down_revision = "b3f8b3e51eb3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_party_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("area", sa.String(length=50), nullable=False),
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
        sa.UniqueConstraint(
            "tenant_id",
            "case_id",
            name="uq_case_party_states_tenant_case",
        ),
    )
    op.create_index(
        op.f("ix_case_party_states_case_id"),
        "case_party_states",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_party_states_case_id_updated_at",
        "case_party_states",
        ["case_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_party_states_tenant_id"),
        "case_party_states",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "case_parties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("party_state_id", sa.Integer(), nullable=False),
        sa.Column("party_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("party_type", sa.String(length=50), nullable=False),
        sa.Column("document_id", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_original_party", sa.Boolean(), nullable=False),
        sa.Column("party_metadata", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["party_state_id"],
            ["case_party_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "party_state_id",
            "party_key",
            name="uq_case_parties_tenant_state_party_key",
        ),
    )
    op.create_index(
        op.f("ix_case_parties_party_state_id"),
        "case_parties",
        ["party_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_parties_state_status",
        "case_parties",
        ["party_state_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_parties_tenant_id"),
        "case_parties",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "case_party_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("party_state_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("occurred_on", sa.String(length=50), nullable=True),
        sa.Column("party_keys", sa.JSON(), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["party_state_id"],
            ["case_party_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_case_party_events_party_state_id"),
        "case_party_events",
        ["party_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_party_events_state_created_at",
        "case_party_events",
        ["party_state_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_case_party_events_state_event_type",
        "case_party_events",
        ["party_state_id", "event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_party_events_tenant_id"),
        "case_party_events",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "case_party_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("party_state_id", sa.Integer(), nullable=False),
        sa.Column("source_party_key", sa.String(length=100), nullable=False),
        sa.Column("target_party_key", sa.String(length=100), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.String(length=50), nullable=True),
        sa.Column("ended_at", sa.String(length=50), nullable=True),
        sa.Column("relationship_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["party_state_id"],
            ["case_party_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_case_party_relationships_party_state_id"),
        "case_party_relationships",
        ["party_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_party_relationships_state_type",
        "case_party_relationships",
        ["party_state_id", "relationship_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_party_relationships_tenant_id"),
        "case_party_relationships",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "case_party_representatives",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("party_state_id", sa.Integer(), nullable=False),
        sa.Column("represented_party_key", sa.String(length=100), nullable=False),
        sa.Column("representative_party_key", sa.String(length=100), nullable=False),
        sa.Column("representation_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.String(length=50), nullable=True),
        sa.Column("ended_at", sa.String(length=50), nullable=True),
        sa.Column("representative_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["party_state_id"],
            ["case_party_states.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_case_party_representatives_party_state_id"),
        "case_party_representatives",
        ["party_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_case_party_representatives_state_keys",
        "case_party_representatives",
        ["party_state_id", "represented_party_key", "representative_party_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_party_representatives_tenant_id"),
        "case_party_representatives",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_case_party_representatives_tenant_id"),
        table_name="case_party_representatives",
    )
    op.drop_index(
        "ix_case_party_representatives_state_keys",
        table_name="case_party_representatives",
    )
    op.drop_index(
        op.f("ix_case_party_representatives_party_state_id"),
        table_name="case_party_representatives",
    )
    op.drop_table("case_party_representatives")

    op.drop_index(
        op.f("ix_case_party_relationships_tenant_id"),
        table_name="case_party_relationships",
    )
    op.drop_index(
        "ix_case_party_relationships_state_type",
        table_name="case_party_relationships",
    )
    op.drop_index(
        op.f("ix_case_party_relationships_party_state_id"),
        table_name="case_party_relationships",
    )
    op.drop_table("case_party_relationships")

    op.drop_index(
        op.f("ix_case_party_events_tenant_id"),
        table_name="case_party_events",
    )
    op.drop_index(
        "ix_case_party_events_state_event_type",
        table_name="case_party_events",
    )
    op.drop_index(
        "ix_case_party_events_state_created_at",
        table_name="case_party_events",
    )
    op.drop_index(
        op.f("ix_case_party_events_party_state_id"),
        table_name="case_party_events",
    )
    op.drop_table("case_party_events")

    op.drop_index(
        op.f("ix_case_parties_tenant_id"),
        table_name="case_parties",
    )
    op.drop_index(
        "ix_case_parties_state_status",
        table_name="case_parties",
    )
    op.drop_index(
        op.f("ix_case_parties_party_state_id"),
        table_name="case_parties",
    )
    op.drop_table("case_parties")

    op.drop_index(
        op.f("ix_case_party_states_tenant_id"),
        table_name="case_party_states",
    )
    op.drop_index(
        "ix_case_party_states_case_id_updated_at",
        table_name="case_party_states",
    )
    op.drop_index(
        op.f("ix_case_party_states_case_id"),
        table_name="case_party_states",
    )
    op.drop_table("case_party_states")
