from app.modules.document_factory.contracts import PartyData, PleadingDraft
from app.modules.parties_succession import (
    CaseParty,
    PartiesSuccessionService,
    PartyRelationship,
    PartyRepresentative,
)


def _build_sample_draft() -> PleadingDraft:
    return PleadingDraft(
        area="trabalhista",
        pleading_type="peticao_inicial",
        title="Petição Inicial Trabalhista",
        parties=[
            PartyData(
                role="claimant",
                name="João da Silva",
                document_id="11111111111",
                metadata={"party_key": "claimant_1", "party_type": "person"},
            ),
            PartyData(
                role="respondent",
                name="Empresa XPTO Ltda",
                document_id="12345678000199",
                metadata={"party_key": "respondent_1", "party_type": "company"},
            ),
        ],
        sections=[
            {"key": "facts", "title": "Fatos", "content": "Resumo dos fatos."},
        ],
        metadata={
            "case_id": 10,
            "tenant_id": 20,
            "user_id": 30,
        },
    )


def test_build_state_from_draft_creates_initial_case_party_state() -> None:
    service = PartiesSuccessionService()
    draft = _build_sample_draft()

    state = service.build_state_from_draft(draft)

    assert state.area == "trabalhista"
    assert state.case_id == 10
    assert state.tenant_id == 20
    assert len(state.parties) == 2
    assert state.parties[0].key == "claimant_1"
    assert state.parties[1].key == "respondent_1"
    assert len(state.events) == 1
    assert state.events[0].event_type == "initial_case_import"


def test_register_succession_preserves_original_party_and_links_successor() -> None:
    service = PartiesSuccessionService()
    state = service.build_state_from_draft(_build_sample_draft())

    successor = CaseParty(
        key="claimant_successor_1",
        name="Maria da Silva",
        role="claimant",
        party_type="person",
        document_id="22222222222",
        metadata={"qualification": "herdeira sucessora"},
    )

    updated_state = service.register_succession(
        state,
        original_party_key="claimant_1",
        successor_party=successor,
        occurred_on="2026-03-19",
        description="Falecimento da parte originária com habilitação de sucessora.",
    )

    original_party = next(p for p in updated_state.parties if p.key == "claimant_1")
    successor_party = next(p for p in updated_state.parties if p.key == "claimant_successor_1")
    succession_event = updated_state.events[-1]
    succession_relationship = updated_state.relationships[-1]

    assert original_party.status == "succeeded"
    assert original_party.metadata["succession_preserved"] is True
    assert original_party.metadata["successor_party_key"] == "claimant_successor_1"

    assert successor_party.is_original_party is False
    assert successor_party.metadata["origin_party_key"] == "claimant_1"

    assert succession_event.event_type == "succession_registered"
    assert succession_event.party_keys == ["claimant_1", "claimant_successor_1"]

    assert succession_relationship.source_party_key == "claimant_1"
    assert succession_relationship.target_party_key == "claimant_successor_1"
    assert succession_relationship.relationship_type == "procedural_successor"


def test_add_representative_and_relationship_register_events() -> None:
    service = PartiesSuccessionService()
    state = service.build_state_from_draft(_build_sample_draft())

    state = service.add_party(
        state,
        CaseParty(
            key="lawyer_1",
            name="Dra. Ana Souza",
            role="lawyer",
            party_type="person",
            document_id="33333333333",
        ),
    )

    state = service.add_representative(
        state,
        PartyRepresentative(
            represented_party_key="claimant_1",
            representative_party_key="lawyer_1",
            representation_type="attorney",
        ),
        occurred_on="2026-03-19",
    )

    state = service.add_relationship(
        state,
        PartyRelationship(
            source_party_key="claimant_1",
            target_party_key="respondent_1",
            relationship_type="opposing_party",
        ),
        occurred_on="2026-03-19",
    )

    assert len(state.representatives) == 1
    assert state.representatives[0].representation_type == "attorney"

    assert len(state.relationships) == 1
    assert state.relationships[0].relationship_type == "opposing_party"

    event_types = [event.event_type for event in state.events]
    assert "party_added" in event_types
    assert "representative_added" in event_types
    assert "relationship_added" in event_types


def test_update_party_status_registers_event() -> None:
    service = PartiesSuccessionService()
    state = service.build_state_from_draft(_build_sample_draft())

    updated_state = service.update_party_status(
        state,
        party_key="respondent_1",
        status="inactive",
        title="Parte temporariamente inativa",
        description="Situação registrada para acompanhamento processual.",
        occurred_on="2026-03-19",
        metadata={"reason": "corporate_change"},
    )

    respondent = next(p for p in updated_state.parties if p.key == "respondent_1")
    last_event = updated_state.events[-1]

    assert respondent.status == "inactive"
    assert respondent.metadata["last_status"] == "inactive"
    assert last_event.event_type == "party_status_updated"
    assert last_event.metadata["reason"] == "corporate_change"


def test_build_document_snapshot_separates_active_and_historical_parties() -> None:
    service = PartiesSuccessionService()
    state = service.build_state_from_draft(_build_sample_draft())

    state = service.add_party(
        state,
        CaseParty(
            key="lawyer_1",
            name="Dra. Ana Souza",
            role="lawyer",
            party_type="person",
            document_id="33333333333",
        ),
    )

    state = service.add_representative(
        state,
        PartyRepresentative(
            represented_party_key="claimant_1",
            representative_party_key="lawyer_1",
            representation_type="attorney",
        ),
        occurred_on="2026-03-19",
    )

    state = service.register_succession(
        state,
        original_party_key="claimant_1",
        successor_party=CaseParty(
            key="claimant_successor_1",
            name="Maria da Silva",
            role="claimant",
            party_type="person",
            document_id="22222222222",
        ),
        occurred_on="2026-03-19",
    )

    snapshot = service.build_document_snapshot(state)

    active_keys = [party.key for party in snapshot.active_parties]
    historical_keys = [party.key for party in snapshot.historical_parties]

    assert "claimant_successor_1" in active_keys
    assert "respondent_1" in active_keys
    assert "lawyer_1" in active_keys
    assert "claimant_1" in historical_keys

    assert len(snapshot.representatives) == 1
    assert snapshot.representatives[0].representative_party_key == "lawyer_1"

    assert len(snapshot.succession_relationships) == 1
    assert snapshot.succession_relationships[0].target_party_key == "claimant_successor_1"

    assert snapshot.metadata["case_id"] == 10
    assert snapshot.metadata["tenant_id"] == 20
