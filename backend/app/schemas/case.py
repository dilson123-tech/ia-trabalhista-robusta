from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CaseBase(BaseModel):
    case_number: str
    title: str
    description: str | None = None
    status: str = "draft"


class CaseCreate(CaseBase):
    pass


class CaseOut(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
