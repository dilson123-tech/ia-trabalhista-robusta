from datetime import datetime
from pydantic import BaseModel, Field


class EditableSectionIn(BaseModel):
    key: str
    title: str
    content: str
    source: str = "ai"
    status: str = "draft"
    metadata: dict = Field(default_factory=dict)


class EditableDocumentCreate(BaseModel):
    case_id: int
    area: str
    document_type: str
    title: str
    sections: list[EditableSectionIn] = Field(default_factory=list)
    notes: str | None = None
    metadata: dict = Field(default_factory=dict)


class EditableDocumentVersionCreate(BaseModel):
    sections: list[EditableSectionIn] = Field(default_factory=list)
    notes: str | None = None
    metadata: dict = Field(default_factory=dict)
    approved: bool = False


class EditableDocumentVersionOut(BaseModel):
    id: int
    editable_document_id: int
    tenant_id: int
    version_number: int
    approved: bool
    notes: str | None = None
    sections: list[dict] = Field(default_factory=list)
    version_metadata: dict = Field(default_factory=dict)
    created_by_user_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class EditableDocumentOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    created_by_user_id: int | None = None
    area: str
    document_type: str
    title: str
    status: str
    current_version_number: int
    document_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EditableDocumentDetailOut(EditableDocumentOut):
    versions: list[EditableDocumentVersionOut] = Field(default_factory=list)
