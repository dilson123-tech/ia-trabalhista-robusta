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
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseAnalysisOut(BaseModel):
    """Saída pública de uma análise de caso (histórico)."""

    id: int
    case_id: int
    created_at: datetime

    class Config:
        from_attributes = True
