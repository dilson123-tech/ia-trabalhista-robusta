"""add tenant_id to cases (clean)

Revision ID: c2b63c79278f
Revises: a03f969eccd7
Create Date: 2026-02-15 17:41:48.197266

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2b63c79278f'
down_revision = 'a03f969eccd7'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1️⃣ adicionar como nullable
    op.add_column(
        "cases",
        sa.Column("tenant_id", sa.Integer(), nullable=True),
    )

    # 2️⃣ preencher registros existentes com tenant 1
    op.execute("UPDATE cases SET tenant_id = 1 WHERE tenant_id IS NULL")

    # 3️⃣ tornar NOT NULL
    op.alter_column("cases", "tenant_id", nullable=False)

    # FK e índice
    op.create_foreign_key(
        "fk_cases_tenant_id",
        "cases",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_cases_tenant_id", "cases", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_cases_tenant_id", table_name="cases")
    op.drop_constraint("fk_cases_tenant_id", "cases", type_="foreignkey")
    op.drop_column("cases", "tenant_id")
