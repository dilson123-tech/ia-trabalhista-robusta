from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


EvidenceChecklistStatus = Literal[
    "pending",
    "requested",
    "received",
    "validated",
    "waived",
    "needs_review",
]

EvidenceChecklistPriority = Literal[
    "low",
    "normal",
    "high",
    "urgent",
]

EvidenceChecklistCategory = Literal[
    "documento",
    "prova_documental",
    "prova_oral",
    "prova_tecnica",
    "comprovante",
    "contrato",
    "mensagem",
    "foto_video",
    "documento_pessoal",
    "outro",
]


class CaseEvidenceChecklistCreate(BaseModel):
    item_key: str | None = Field(default=None, max_length=120)
    title: str = Field(min_length=2, max_length=240)
    category: EvidenceChecklistCategory = "outro"
    status: EvidenceChecklistStatus = "pending"
    priority: EvidenceChecklistPriority = "normal"
    requested_from: str | None = Field(default=None, max_length=160)
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=3000)
    attachment_id: int | None = None
    metadata: dict = Field(default_factory=dict)


class CaseEvidenceChecklistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=240)
    category: EvidenceChecklistCategory | None = None
    status: EvidenceChecklistStatus | None = None
    priority: EvidenceChecklistPriority | None = None
    requested_from: str | None = Field(default=None, max_length=160)
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=3000)
    attachment_id: int | None = None
    metadata: dict = Field(default_factory=dict)


class CaseEvidenceChecklistOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    attachment_id: int | None = None
    item_key: str
    title: str
    category: str
    status: str
    priority: str
    requested_from: str | None = None
    due_date: date | None = None
    notes: str | None = None
    checklist_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
