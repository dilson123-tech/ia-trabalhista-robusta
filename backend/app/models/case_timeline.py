from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaseTimelineItem(Base):
    __tablename__ = "case_timeline_items"

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

    event_date: Mapped[str | None] = mapped_column(String(80), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    related_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_witness: Mapped[str | None] = mapped_column(String(240), nullable=True)
    pending_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)
    timeline_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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
        Index(
            "ix_case_timeline_items_case_order",
            "case_id",
            "sort_order",
            "id",
        ),
        Index(
            "ix_case_timeline_items_case_created_at",
            "case_id",
            "created_at",
        ),
    )
