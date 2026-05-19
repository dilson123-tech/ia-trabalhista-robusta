from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaseAttachment(Base):
    __tablename__ = "case_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(700), nullable=False, unique=True)

    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped[str] = mapped_column(String(60), nullable=False, default="outro")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "case_id", "stored_filename", name="uq_case_attachments_tenant_case_file"),
    )
