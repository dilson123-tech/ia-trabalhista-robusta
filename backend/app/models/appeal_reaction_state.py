from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppealReactionStateModel(Base):
    __tablename__ = "appeal_reaction_states"

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

    area: Mapped[str] = mapped_column(String(50), nullable=False)

    decision_type: Mapped[str] = mapped_column(String(50), nullable=False, default="sentenca")
    decision_title: Mapped[str] = mapped_column(String(255), nullable=False, default="Decisão judicial")
    decision_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    state_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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
            "ix_appeal_reaction_states_case_id_updated_at",
            "case_id",
            "updated_at",
        ),
        Index(
            "ix_appeal_reaction_states_case_decision_date",
            "case_id",
            "decision_date",
        ),
    )


class AppealDecisionPointModel(Base):
    __tablename__ = "appeal_decision_points"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appeal_reaction_state_id: Mapped[int] = mapped_column(
        ForeignKey("appeal_reaction_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    point_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, default="unfavorable")
    legal_effect: Mapped[str | None] = mapped_column(String(255), nullable=True)
    point_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "appeal_reaction_state_id",
            "point_key",
            name="uq_appeal_decision_points_tenant_state_point_key",
        ),
        Index(
            "ix_appeal_decision_points_state_outcome",
            "appeal_reaction_state_id",
            "outcome",
        ),
    )


class AppealDeadlineModel(Base):
    __tablename__ = "appeal_deadlines"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appeal_reaction_state_id: Mapped[int] = mapped_column(
        ForeignKey("appeal_reaction_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    deadline_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    deadline_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "appeal_reaction_state_id",
            "deadline_key",
            name="uq_appeal_deadlines_tenant_state_deadline_key",
        ),
        Index(
            "ix_appeal_deadlines_state_status",
            "appeal_reaction_state_id",
            "status",
        ),
    )


class AppealStrategyItemModel(Base):
    __tablename__ = "appeal_strategy_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appeal_reaction_state_id: Mapped[int] = mapped_column(
        ForeignKey("appeal_reaction_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    strategy_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_point_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[str] = mapped_column(String(30), nullable=False, default="normal")
    strategy_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "appeal_reaction_state_id",
            "strategy_key",
            name="uq_appeal_strategy_items_tenant_state_strategy_key",
        ),
        Index(
            "ix_appeal_strategy_items_state_priority",
            "appeal_reaction_state_id",
            "priority",
        ),
    )


class AppealDraftRefModel(Base):
    __tablename__ = "appeal_draft_refs"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appeal_reaction_state_id: Mapped[int] = mapped_column(
        ForeignKey("appeal_reaction_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draft_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_appeal_draft_refs_state_status",
            "appeal_reaction_state_id",
            "status",
        ),
    )
