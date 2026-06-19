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


class EditableDocumentFinalVerdictOut(BaseModel):
    document_id: int
    title: str
    version_number: int
    analysis_source: str
    export_status: str
    content_status: str
    final_decision: str
    risk_level: str
    approved_points: list[str] = Field(default_factory=list)
    critical_pending: list[str] = Field(default_factory=list)
    non_critical_pending: list[str] = Field(default_factory=list)
    missing_blocks: list[str] = Field(default_factory=list)
    placeholders: list[str] = Field(default_factory=list)
    required_data_pending: list[str] = Field(default_factory=list)
    cause_value_analysis: dict = Field(default_factory=dict)
    fact_proof_request_links: list[dict] = Field(default_factory=list)
    benchmark_analysis: dict = Field(default_factory=dict)
    preliminary_draft_analysis: dict = Field(default_factory=dict)
    operational_text_flags: list[str] = Field(default_factory=list)
    next_step: str
    summary: str
