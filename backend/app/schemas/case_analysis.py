from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class CaseAnalysisBase(BaseModel):
    risk_level: str = Field(..., examples=["low", "medium", "high"])
    summary: str
    issues: Dict[str, Any]
    next_steps: List[str]


class CaseAnalysisCreate(CaseAnalysisBase):
    case_id: int


class CaseAnalysisOut(CaseAnalysisBase):
    id: int
    case_id: int
    created_at: datetime

    class Config:
        from_attributes = True
