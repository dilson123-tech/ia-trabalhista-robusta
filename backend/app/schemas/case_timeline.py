from datetime import datetime

from pydantic import BaseModel, Field


class CaseTimelineCreate(BaseModel):
    event_date: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=2, max_length=5000)
    related_evidence: str | None = Field(default=None, max_length=3000)
    related_witness: str | None = Field(default=None, max_length=240)
    pending_note: str | None = Field(default=None, max_length=3000)
    sort_order: int = 0
    metadata: dict = Field(default_factory=dict)


class CaseTimelineUpdate(BaseModel):
    event_date: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, min_length=2, max_length=240)
    description: str | None = Field(default=None, min_length=2, max_length=5000)
    related_evidence: str | None = Field(default=None, max_length=3000)
    related_witness: str | None = Field(default=None, max_length=240)
    pending_note: str | None = Field(default=None, max_length=3000)
    sort_order: int | None = None
    metadata: dict = Field(default_factory=dict)


class CaseTimelineOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    event_date: str | None = None
    title: str
    description: str
    related_evidence: str | None = None
    related_witness: str | None = None
    pending_note: str | None = None
    sort_order: int
    timeline_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
