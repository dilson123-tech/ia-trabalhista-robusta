from datetime import datetime
from pydantic import BaseModel, Field


class CasePartyIn(BaseModel):
    key: str
    name: str
    role: str
    party_type: str = "person"
    document_id: str | None = None
    status: str = "active"
    is_original_party: bool = True
    metadata: dict = Field(default_factory=dict)


class PartyRepresentativeIn(BaseModel):
    represented_party_key: str
    representative_party_key: str
    representation_type: str = "legal"
    status: str = "active"
    started_at: str | None = None
    ended_at: str | None = None
    metadata: dict = Field(default_factory=dict)


class PartyRelationshipIn(BaseModel):
    source_party_key: str
    target_party_key: str
    relationship_type: str
    status: str = "active"
    started_at: str | None = None
    ended_at: str | None = None
    metadata: dict = Field(default_factory=dict)


class PartyEventOut(BaseModel):
    id: int
    event_type: str
    title: str
    description: str | None = None
    occurred_on: str | None = None
    party_keys: list[str] = Field(default_factory=list)
    event_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class CasePartyOut(BaseModel):
    id: int
    tenant_id: int
    party_state_id: int
    party_key: str
    name: str
    role: str
    party_type: str
    document_id: str | None = None
    status: str
    is_original_party: bool
    party_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartyRepresentativeOut(BaseModel):
    id: int
    tenant_id: int
    party_state_id: int
    represented_party_key: str
    representative_party_key: str
    representation_type: str
    status: str
    started_at: str | None = None
    ended_at: str | None = None
    representative_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class PartyRelationshipOut(BaseModel):
    id: int
    tenant_id: int
    party_state_id: int
    source_party_key: str
    target_party_key: str
    relationship_type: str
    status: str
    started_at: str | None = None
    ended_at: str | None = None
    relationship_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class CasePartyStateCreate(BaseModel):
    case_id: int
    area: str
    parties: list[CasePartyIn] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class RegisterSuccessionIn(BaseModel):
    original_party_key: str
    successor_party: CasePartyIn
    relationship_type: str = "procedural_successor"
    occurred_on: str | None = None
    description: str | None = None


class PartyStatusUpdateIn(BaseModel):
    party_key: str
    status: str
    title: str
    description: str | None = None
    occurred_on: str | None = None
    metadata: dict = Field(default_factory=dict)


class CasePartyStateOut(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    area: str
    state_metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CasePartyStateDetailOut(CasePartyStateOut):
    parties: list[CasePartyOut] = Field(default_factory=list)
    representatives: list[PartyRepresentativeOut] = Field(default_factory=list)
    relationships: list[PartyRelationshipOut] = Field(default_factory=list)
    events: list[PartyEventOut] = Field(default_factory=list)


class DocumentPartySnapshotOut(BaseModel):
    active_parties: list[CasePartyOut] = Field(default_factory=list)
    historical_parties: list[CasePartyOut] = Field(default_factory=list)
    representatives: list[PartyRepresentativeOut] = Field(default_factory=list)
    succession_relationships: list[PartyRelationshipOut] = Field(default_factory=list)
    events: list[PartyEventOut] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
