from datetime import datetime
from pydantic import BaseModel


class CaseBase(BaseModel):
    case_number: str
    title: str
    description: str | None = None
    status: str = "draft"


class CaseCreate(CaseBase):
    pass


class CaseOut(CaseBase):
    tenant_id: int
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


from typing import Literal


class CaseStatusUpdate(BaseModel):
    status: Literal["draft", "active", "review", "archived"]


class DemoCleanupOut(BaseModel):
    deleted_cases: int
    deleted_analyses: int
