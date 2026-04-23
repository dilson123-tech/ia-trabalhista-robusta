from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func

from app.db.base import Base


class BillingRequest(Base):
    __tablename__ = "billing_requests"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_plan_type = Column(String(20), nullable=False)
    current_plan_type = Column(String(20), nullable=False, default="basic")

    billing_reason = Column(String(30), nullable=False, default="plan_upgrade")
    payment_method = Column(String(20), nullable=False, default="pending")
    payment_provider = Column(String(30), nullable=False, default="manual")

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="BRL")

    status = Column(String(30), nullable=False, default="requested")

    provider_reference = Column(String(120), nullable=True)
    checkout_url = Column(String(500), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "requested_plan_type in ('basic','pro','office')",
            name="ck_billing_requests_requested_plan_type",
        ),
        CheckConstraint(
            "current_plan_type in ('basic','pro','office')",
            name="ck_billing_requests_current_plan_type",
        ),
        CheckConstraint(
            "billing_reason in ('plan_upgrade','plan_downgrade','plan_renewal')",
            name="ck_billing_requests_reason",
        ),
        CheckConstraint(
            "payment_method in ('pending','pix','credit_card','debit_card')",
            name="ck_billing_requests_payment_method",
        ),
        CheckConstraint(
            "status in ('requested','checkout_pending','paid','expired','canceled','failed')",
            name="ck_billing_requests_status",
        ),
    )
