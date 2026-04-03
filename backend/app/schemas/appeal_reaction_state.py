from datetime import datetime
from pydantic import BaseModel, Field


class DecisionPointIn(BaseModel):
    key: str
    title: str
    description: str
    outcome: str = "unfavorable"
    legal_effect: str | None = None
    metadata: dict = Field(default_factory=dict)


class JudicialDecisionIn(BaseModel):
    decision_type: str = "sentenca"
    title: str = "Decisão judicial"
    summary: str | None = None
    decision_date: str | None = None
    unfavorable_points: list[DecisionPointIn] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class AppealDeadlineIn(BaseModel):
    key: str
    title: str
    due_date: str | None = None
    status: str = "pending"
    metadata: dict = Field(default_factory=dict)


class AppealStrategyItemIn(BaseModel):
    key: str
    title: str
    description: str
    target_point_keys: list[str] = Field(default_factory=list)
    priority: str = "normal"
    metadata: dict = Field(default_factory=dict)


class AppealDraftRefIn(BaseModel):
    document_type: str
    title: str
    status: str = "draft"
    version: int | None = None
    metadata: dict = Field(default_factory=dict)


class AppealReactionStateCreate(BaseModel):
    case_id: int
    area: str
    source_decision: JudicialDecisionIn
    metadata: dict = Field(default_factory=dict)


class DecisionPointOut(BaseModel):
    id: int
    tenant_id: int
    appeal_reaction_state_id: int
    point_key: str
    title: str
    description: str
    outcome: str
    legal_effect: str | None = None
    point_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AppealDeadlineOut(BaseModel):
    id: int
    tenant_id: int
    appeal_reaction_state_id: int
    deadline_key: str
    title: str
    due_date: str | None = None
    status: str
    deadline_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AppealStrategyItemOut(BaseModel):
    id: int
    tenant_id: int
    appeal_reaction_state_id: int
    strategy_key: str
    title: str
    description: str
    target_point_keys: list[str] = Field(default_factory=list)
    priority: str
    strategy_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AppealDraftRefOut(BaseModel):
    id: int
    tenant_id: int
    appeal_reaction_state_id: int
    document_type: str
    title: str
    status: str
    version: int | None = None
    draft_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AppealReactionStateOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    area: str
    decision_type: str
    decision_title: str
    decision_summary: str | None = None
    decision_date: str | None = None
    decision_metadata: dict = Field(default_factory=dict)
    state_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppealReactionStateDetailOut(AppealReactionStateOut):
    decision_points: list[DecisionPointOut] = Field(default_factory=list)
    deadlines: list[AppealDeadlineOut] = Field(default_factory=list)
    strategy_items: list[AppealStrategyItemOut] = Field(default_factory=list)
    appeal_drafts: list[AppealDraftRefOut] = Field(default_factory=list)


class AppealReactionSummaryOut(BaseModel):
    area: str
    case_id: int | None = None
    tenant_id: int | None = None
    decision_type: str
    decision_title: str
    decision_summary: str | None = None

    executive_headline: str = ""
    executive_summary: str = ""
    recommendation: str = ""
    urgency_level: str = "moderada"
    appeal_readiness: str = "parcial"

    deadline_status: dict = Field(default_factory=dict)
    priority_strategy: dict = Field(default_factory=dict)
    evidence_focus: list[dict] = Field(default_factory=list)
    risk_alerts: list[str] = Field(default_factory=list)
    counts: dict = Field(default_factory=dict)

    unfavorable_points: list[dict] = Field(default_factory=list)
    deadlines: list[dict] = Field(default_factory=list)
    strategy_items: list[dict] = Field(default_factory=list)
    appeal_drafts: list[dict] = Field(default_factory=list)
