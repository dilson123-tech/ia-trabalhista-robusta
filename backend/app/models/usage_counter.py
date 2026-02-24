from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func

from app.db.base import Base


class UsageCounter(Base):
    __tablename__ = "usage_counters"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Armazenar como DATE (sempre o 1º dia do mês). Ex: 2026-02-01
    month = Column(Date, nullable=False)

    cases_created = Column(Integer, nullable=False, server_default="0")
    ai_analyses_generated = Column(Integer, nullable=False, server_default="0")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "month", name="uq_usage_counters_tenant_month"),
    )
