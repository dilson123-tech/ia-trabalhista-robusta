from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


CaseAttachmentCategory = Literal[
    "foto",
    "video",
    "pdf",
    "documento_medico",
    "notificacao",
    "documento_pessoal",
    "contrato",
    "testemunha",
    "outro",
]


class CaseAttachmentOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    original_filename: str
    mime_type: str | None = None
    file_size_bytes: int
    category: str
    description: str | None = None
    event_date: date | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseAttachmentUpdate(BaseModel):
    category: CaseAttachmentCategory | None = None
    description: str | None = Field(default=None, max_length=2000)
    event_date: date | None = None
