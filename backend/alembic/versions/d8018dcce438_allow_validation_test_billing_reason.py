"""allow validation_test billing reason

Revision ID: d8018dcce438
Revises: 9f2c4b7d1e10
Create Date: 2026-04-28 15:20:54.526353

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd8018dcce438'
down_revision = '9f2c4b7d1e10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE billing_requests
    DROP CONSTRAINT IF EXISTS ck_billing_requests_reason;
    """)
    op.execute("""
    ALTER TABLE billing_requests
    ADD CONSTRAINT ck_billing_requests_reason
    CHECK (billing_reason IN ('plan_upgrade','plan_downgrade','plan_renewal','validation_test'));
    """)


def downgrade() -> None:
    op.execute("""
    ALTER TABLE billing_requests
    DROP CONSTRAINT IF EXISTS ck_billing_requests_reason;
    """)
    op.execute("""
    ALTER TABLE billing_requests
    ADD CONSTRAINT ck_billing_requests_reason
    CHECK (billing_reason IN ('plan_upgrade','plan_downgrade','plan_renewal'));
    """)
