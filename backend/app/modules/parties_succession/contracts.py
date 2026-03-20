from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.document_factory.contracts import PleadingDraft


@dataclass(slots=True)
class CaseParty:
    key: str
    name: str
    role: str
    party_type: str = "person"
    document_id: str | None = None
    status: str = "active"
    is_original_party: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PartyRepresentative:
    represented_party_key: str
    representative_party_key: str
    representation_type: str = "legal"
    status: str = "active"
    started_at: str | None = None
    ended_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PartyRelationship:
    source_party_key: str
    target_party_key: str
    relationship_type: str
    status: str = "active"
    started_at: str | None = None
    ended_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PartyEvent:
    event_type: str
    title: str
    description: str | None = None
    occurred_on: str | None = None
    party_keys: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CasePartyState:
    area: str
    case_id: int | None = None
    tenant_id: int | None = None
    parties: list[CaseParty] = field(default_factory=list)
    representatives: list[PartyRepresentative] = field(default_factory=list)
    relationships: list[PartyRelationship] = field(default_factory=list)
    events: list[PartyEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentPartySnapshot:
    active_parties: list[CaseParty] = field(default_factory=list)
    historical_parties: list[CaseParty] = field(default_factory=list)
    representatives: list[PartyRepresentative] = field(default_factory=list)
    succession_relationships: list[PartyRelationship] = field(default_factory=list)
    events: list[PartyEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def build_case_party_state_from_draft(draft: PleadingDraft) -> CasePartyState:
    parties: list[CaseParty] = []

    for index, party in enumerate(draft.parties, start=1):
        metadata = dict(party.metadata)
        party_key = metadata.get("party_key") or f"party_{index}"

        parties.append(
            CaseParty(
                key=party_key,
                name=party.name,
                role=party.role,
                party_type=metadata.get("party_type") or "person",
                document_id=party.document_id,
                status=metadata.get("status") or "active",
                is_original_party=metadata.get("is_original_party", True),
                metadata=metadata,
            )
        )

    initial_event = PartyEvent(
        event_type="initial_case_import",
        title="Importação inicial das partes do caso",
        description="Estrutura inicial derivada do draft jurídico.",
        party_keys=[party.key for party in parties],
        metadata={
            "source": "document_factory",
            "draft_type": draft.pleading_type,
        },
    )

    return CasePartyState(
        area=draft.area,
        case_id=draft.metadata.get("case_id"),
        tenant_id=draft.metadata.get("tenant_id"),
        parties=parties,
        events=[initial_event],
        metadata={
            "source": "document_factory",
            "draft_type": draft.pleading_type,
        },
    )
