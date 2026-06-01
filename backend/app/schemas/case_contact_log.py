from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CaseContactType = Literal["whatsapp", "phone", "email", "manual", "other"]
CaseContactDirection = Literal["outgoing", "incoming"]


class CaseContactLogCreate(BaseModel):
    contact_type: CaseContactType = "whatsapp"
    direction: CaseContactDirection = "outgoing"
    summary: str = Field(..., min_length=3, max_length=240)
    note: str | None = Field(default=None, max_length=2000)
    occurred_at: datetime | None = None


class CaseContactLogOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    contact_type: str
    direction: str
    summary: str
    note: str | None = None
    occurred_at: datetime
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
