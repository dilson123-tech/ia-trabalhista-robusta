from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaseAnalysis(Base):
    __tablename__ = "case_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Resultado da análise (rules/IA no futuro)
    risk_level: Mapped[str] = mapped_column(nullable=False)
    summary: Mapped[str] = mapped_column(nullable=False)
    issues: Mapped[dict] = mapped_column(JSON, nullable=False)
    next_steps: Mapped[dict] = mapped_column(JSON, nullable=False)

    analysis: Mapped[dict] = mapped_column(JSON, nullable=False)

    executive_data: Mapped[dict] = mapped_column(JSON, nullable=True)


    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_case_analyses_case_id_created_at", "case_id", "created_at"),
    )
