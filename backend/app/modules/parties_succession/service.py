from __future__ import annotations

from app.modules.document_factory.contracts import PleadingDraft
from app.modules.parties_succession.contracts import (
    CaseParty,
    CasePartyState,
    DocumentPartySnapshot,
    PartyEvent,
    PartyRelationship,
    PartyRepresentative,
    build_case_party_state_from_draft,
)


class PartiesSuccessionService:
    def build_state_from_draft(self, draft: PleadingDraft) -> CasePartyState:
        return build_case_party_state_from_draft(draft)

    def build_document_snapshot(self, state: CasePartyState) -> DocumentPartySnapshot:
        active_parties = [party for party in state.parties if party.status == "active"]
        historical_parties = [party for party in state.parties if party.status != "active"]
        succession_relationships = [
            relationship
            for relationship in state.relationships
            if relationship.relationship_type == "procedural_successor"
        ]

        return DocumentPartySnapshot(
            active_parties=active_parties,
            historical_parties=historical_parties,
            representatives=list(state.representatives),
            succession_relationships=succession_relationships,
            events=list(state.events),
            metadata={
                "area": state.area,
                "case_id": state.case_id,
                "tenant_id": state.tenant_id,
                "source": "parties_succession_service",
            },
        )

    def add_party(self, state: CasePartyState, party: CaseParty) -> CasePartyState:
        self._ensure_party_key_is_unique(state, party.key)
        state.parties.append(party)
        state.events.append(
            PartyEvent(
                event_type="party_added",
                title=f"Parte adicionada: {party.name}",
                party_keys=[party.key],
                metadata={
                    "role": party.role,
                    "source": "parties_succession_service",
                },
            )
        )
        return state

    def add_representative(
        self,
        state: CasePartyState,
        representative: PartyRepresentative,
        *,
        occurred_on: str | None = None,
    ) -> CasePartyState:
        self._get_party(state, representative.represented_party_key)
        self._get_party(state, representative.representative_party_key)

        state.representatives.append(representative)
        state.events.append(
            PartyEvent(
                event_type="representative_added",
                title="Representação vinculada à parte",
                occurred_on=occurred_on,
                party_keys=[
                    representative.represented_party_key,
                    representative.representative_party_key,
                ],
                metadata={
                    "representation_type": representative.representation_type,
                    "source": "parties_succession_service",
                },
            )
        )
        return state

    def add_relationship(
        self,
        state: CasePartyState,
        relationship: PartyRelationship,
        *,
        occurred_on: str | None = None,
    ) -> CasePartyState:
        self._get_party(state, relationship.source_party_key)
        self._get_party(state, relationship.target_party_key)

        state.relationships.append(relationship)
        state.events.append(
            PartyEvent(
                event_type="relationship_added",
                title="Vínculo entre partes registrado",
                occurred_on=occurred_on,
                party_keys=[
                    relationship.source_party_key,
                    relationship.target_party_key,
                ],
                metadata={
                    "relationship_type": relationship.relationship_type,
                    "source": "parties_succession_service",
                },
            )
        )
        return state

    def update_party_status(
        self,
        state: CasePartyState,
        *,
        party_key: str,
        status: str,
        title: str,
        description: str | None = None,
        occurred_on: str | None = None,
        metadata: dict | None = None,
    ) -> CasePartyState:
        party = self._get_party(state, party_key)
        party.status = status
        party.metadata["last_status"] = status

        state.events.append(
            PartyEvent(
                event_type="party_status_updated",
                title=title,
                description=description,
                occurred_on=occurred_on,
                party_keys=[party_key],
                metadata={
                    "status": status,
                    "source": "parties_succession_service",
                    **(metadata or {}),
                },
            )
        )
        return state

    def register_succession(
        self,
        state: CasePartyState,
        *,
        original_party_key: str,
        successor_party: CaseParty,
        relationship_type: str = "procedural_successor",
        occurred_on: str | None = None,
        description: str | None = None,
    ) -> CasePartyState:
        original_party = self._get_party(state, original_party_key)
        self._ensure_party_key_is_unique(state, successor_party.key)

        original_party.status = "succeeded"
        original_party.metadata["succession_preserved"] = True
        original_party.metadata["successor_party_key"] = successor_party.key

        successor_party.is_original_party = False
        successor_party.metadata.setdefault("origin_party_key", original_party_key)
        successor_party.metadata.setdefault("created_by", "parties_succession_service")

        state.parties.append(successor_party)
        state.relationships.append(
            PartyRelationship(
                source_party_key=original_party_key,
                target_party_key=successor_party.key,
                relationship_type=relationship_type,
                status="active",
                started_at=occurred_on,
                metadata={
                    "source": "parties_succession_service",
                    "preserved_history": True,
                },
            )
        )
        state.events.append(
            PartyEvent(
                event_type="succession_registered",
                title="Sucessão processual registrada",
                description=description
                or "A parte originária foi preservada no histórico e vinculada ao sucessor.",
                occurred_on=occurred_on,
                party_keys=[original_party_key, successor_party.key],
                metadata={
                    "relationship_type": relationship_type,
                    "preserved_history": True,
                    "source": "parties_succession_service",
                },
            )
        )
        return state

    def _get_party(self, state: CasePartyState, party_key: str) -> CaseParty:
        for party in state.parties:
            if party.key == party_key:
                return party
        raise ValueError(f"Party with key '{party_key}' was not found")

    def _ensure_party_key_is_unique(self, state: CasePartyState, party_key: str) -> None:
        for party in state.parties:
            if party.key == party_key:
                raise ValueError(f"Party with key '{party_key}' already exists")
