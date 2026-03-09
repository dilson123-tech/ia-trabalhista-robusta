from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # string + CHECK (evita dor com Postgres ENUM em migração; mantém “enum no banco” na prática)
    status = Column(String(20), nullable=False, default="trial")
    plan_type = Column(String(20), nullable=False, default="basic")

    case_limit = Column(Integer, nullable=False, default=10)
    active = Column(Boolean, nullable=False, default=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_subscriptions_tenant"),
        CheckConstraint("status in ('active','trial','canceled')", name="ck_subscriptions_status"),
        CheckConstraint("plan_type in ('basic','pro','office')", name="ck_subscriptions_plan_type"),
    )
