from __future__ import annotations

import datetime as dt
from typing import Optional, Dict, Any

from sqlalchemy import String, DateTime, ForeignKey, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BusinessAuditLog(Base):
    __tablename__ = "business_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
