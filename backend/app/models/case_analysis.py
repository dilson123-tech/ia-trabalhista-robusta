from __future__ import annotations

import datetime as dt
from sqlalchemy import ForeignKey, String, Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CaseAnalysis(Base):
    __tablename__ = "case_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    issues: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    next_steps: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    case = relationship(
        "Case",
        backref="analyses",
        lazy="joined",
    )
