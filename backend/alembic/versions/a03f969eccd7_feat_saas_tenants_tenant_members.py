"""feat(saas): tenants + tenant_members (clean)"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a03f969eccd7"
down_revision = "a8232a6b8077"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    op.create_index(
        "ix_tenants_name",
        "tenants",
        ["name"],
        unique=False,
    )

    op.create_table(
        "tenant_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
    )

    op.create_index(
        "ix_tenant_members_tenant_id",
        "tenant_members",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        "ix_tenant_members_user_id",
        "tenant_members",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_members_user_id", table_name="tenant_members")
    op.drop_index("ix_tenant_members_tenant_id", table_name="tenant_members")
    op.drop_table("tenant_members")

    op.drop_index("ix_tenants_name", table_name="tenants")
    op.drop_table("tenants")
