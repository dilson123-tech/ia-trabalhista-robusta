"""create billing_requests table

Revision ID: 9f2c4b7d1e10
Revises: e385c92a9ee2
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f2c4b7d1e10"
down_revision = "e385c92a9ee2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_plan_type", sa.String(length=20), nullable=False),
        sa.Column("current_plan_type", sa.String(length=20), nullable=False, server_default="basic"),
        sa.Column("billing_reason", sa.String(length=30), nullable=False, server_default="plan_upgrade"),
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("payment_provider", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="BRL"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="requested"),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("checkout_url", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "requested_plan_type in ('basic','pro','office')",
            name="ck_billing_requests_requested_plan_type",
        ),
        sa.CheckConstraint(
            "current_plan_type in ('basic','pro','office')",
            name="ck_billing_requests_current_plan_type",
        ),
        sa.CheckConstraint(
            "billing_reason in ('plan_upgrade','plan_downgrade','plan_renewal')",
            name="ck_billing_requests_reason",
        ),
        sa.CheckConstraint(
            "payment_method in ('pending','pix','credit_card','debit_card')",
            name="ck_billing_requests_payment_method",
        ),
        sa.CheckConstraint(
            "status in ('requested','checkout_pending','paid','expired','canceled','failed')",
            name="ck_billing_requests_status",
        ),
    )
    op.create_index("ix_billing_requests_tenant_id", "billing_requests", ["tenant_id"])
    op.create_index("ix_billing_requests_status", "billing_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_billing_requests_status", table_name="billing_requests")
    op.drop_index("ix_billing_requests_tenant_id", table_name="billing_requests")
    op.drop_table("billing_requests")
