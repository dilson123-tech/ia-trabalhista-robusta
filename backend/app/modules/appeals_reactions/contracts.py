from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DecisionPoint:
    key: str
    title: str
    description: str
    outcome: str = "unfavorable"
    legal_effect: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JudicialDecision:
    area: str
    case_id: int | None = None
    tenant_id: int | None = None
    decision_type: str = "sentenca"
    title: str = "Decisão judicial"
    summary: str | None = None
    decision_date: str | None = None
    unfavorable_points: list[DecisionPoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppealDeadline:
    key: str
    title: str
    due_date: str | None = None
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppealStrategyItem:
    key: str
    title: str
    description: str
    target_point_keys: list[str] = field(default_factory=list)
    priority: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppealDraftRef:
    document_type: str
    title: str
    status: str = "draft"
    version: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppealReactionState:
    area: str
    case_id: int | None = None
    tenant_id: int | None = None
    source_decision: JudicialDecision | None = None
    deadlines: list[AppealDeadline] = field(default_factory=list)
    strategy_items: list[AppealStrategyItem] = field(default_factory=list)
    appeal_drafts: list[AppealDraftRef] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
