from __future__ import annotations

import datetime as dt
from sqlalchemy import String, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    request_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)

    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    process_time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    username: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)

    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
