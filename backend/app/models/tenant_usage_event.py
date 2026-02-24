from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base


class TenantUsageEvent(Base):
    __tablename__ = "tenant_usage_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
