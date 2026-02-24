"""saas subscriptions + usage counters constraints

Revision ID: 0786ce015a07
Revises: 14a0147aec0b
Create Date: 2026-02-23 23:52:38.658405

"""
from alembic import op
import sqlalchemy as sa


revision = "0786ce015a07"
down_revision = "14a0147aec0b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ✅ Só mexe no que interessa: usage_counters
    op.add_column(
        "usage_counters",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # month: VARCHAR -> DATE (robusto pra 'YYYY-MM' e 'YYYY-MM-DD')
    op.alter_column(
        "usage_counters",
        "month",
        existing_type=sa.VARCHAR(),
        type_=sa.Date(),
        existing_nullable=False,
        postgresql_using="CASE WHEN length(month)=7 THEN to_date(month||'-01','YYYY-MM-DD') ELSE to_date(month,'YYYY-MM-DD') END",
    )

    # renomeia a UQ para o nome novo (sem mexer em índices de outras tabelas)
    op.drop_constraint("uq_tenant_month", "usage_counters", type_="unique")
    op.create_unique_constraint("uq_usage_counters_tenant_month", "usage_counters", ["tenant_id", "month"])


def downgrade() -> None:
    op.drop_constraint("uq_usage_counters_tenant_month", "usage_counters", type_="unique")
    op.create_unique_constraint("uq_tenant_month", "usage_counters", ["tenant_id", "month"])

    op.alter_column(
        "usage_counters",
        "month",
        existing_type=sa.Date(),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )

    op.drop_column("usage_counters", "updated_at")
