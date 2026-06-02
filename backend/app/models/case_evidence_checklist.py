from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaseEvidenceChecklistItem(Base):
    __tablename__ = "case_evidence_checklist_items"

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
    attachment_id: Mapped[int | None] = mapped_column(
        ForeignKey("case_attachments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    item_key: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="outro")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")

    requested_from: Mapped[str | None] = mapped_column(String(160), nullable=True)
    due_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    checklist_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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
        UniqueConstraint(
            "tenant_id",
            "case_id",
            "item_key",
            name="uq_case_evidence_checklist_tenant_case_key",
        ),
        Index(
            "ix_case_evidence_checklist_case_status",
            "case_id",
            "status",
        ),
        Index(
            "ix_case_evidence_checklist_case_priority",
            "case_id",
            "priority",
        ),
    )
