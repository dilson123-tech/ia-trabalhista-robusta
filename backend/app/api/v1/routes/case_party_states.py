from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case
from app.models.case_party_state import (
    CasePartyEventModel,
    CasePartyModel,
    CasePartyRelationshipModel,
    CasePartyRepresentativeModel,
    CasePartyStateModel,
)
from app.modules.parties_succession.contracts import (
    CaseParty,
    CasePartyState,
    PartyEvent,
    PartyRelationship,
    PartyRepresentative,
)
from app.modules.parties_succession.service import PartiesSuccessionService
from app.schemas.case_party_state import (
    CasePartyStateCreate,
    CasePartyStateDetailOut,
    CasePartyStateOut,
    DocumentPartySnapshotOut,
    PartyRelationshipIn,
    PartyRepresentativeIn,
    PartyStatusUpdateIn,
    RegisterSuccessionIn,
)

router = APIRouter(
    prefix="/case-party-states",
    tags=["case-party-states"],
)

service = PartiesSuccessionService()


def _get_state_or_404(
    db: Session,
    *,
    state_id: int,
    tenant_id: int,
) -> CasePartyStateModel:
    state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.id == state_id,
            CasePartyStateModel.tenant_id == tenant_id,
        )
        .first()
    )
    if not state:
        raise HTTPException(status_code=404, detail="Case party state not found")
    return state


def _load_state_bundle(
    db: Session,
    state: CasePartyStateModel,
) -> tuple[
    list[CasePartyModel],
    list[CasePartyRepresentativeModel],
    list[CasePartyRelationshipModel],
    list[CasePartyEventModel],
]:
    parties = (
        db.query(CasePartyModel)
        .filter(
            CasePartyModel.tenant_id == state.tenant_id,
            CasePartyModel.party_state_id == state.id,
        )
        .order_by(CasePartyModel.id.asc())
        .all()
    )
    representatives = (
        db.query(CasePartyRepresentativeModel)
        .filter(
            CasePartyRepresentativeModel.tenant_id == state.tenant_id,
            CasePartyRepresentativeModel.party_state_id == state.id,
        )
        .order_by(CasePartyRepresentativeModel.id.asc())
        .all()
    )
    relationships = (
        db.query(CasePartyRelationshipModel)
        .filter(
            CasePartyRelationshipModel.tenant_id == state.tenant_id,
            CasePartyRelationshipModel.party_state_id == state.id,
        )
        .order_by(CasePartyRelationshipModel.id.asc())
        .all()
    )
    events = (
        db.query(CasePartyEventModel)
        .filter(
            CasePartyEventModel.tenant_id == state.tenant_id,
            CasePartyEventModel.party_state_id == state.id,
        )
        .order_by(CasePartyEventModel.id.asc())
        .all()
    )
    return parties, representatives, relationships, events


def _build_domain_state(
    state: CasePartyStateModel,
    parties: list[CasePartyModel],
    representatives: list[CasePartyRepresentativeModel],
    relationships: list[CasePartyRelationshipModel],
    events: list[CasePartyEventModel],
) -> CasePartyState:
    return CasePartyState(
        area=state.area,
        case_id=state.case_id,
        tenant_id=state.tenant_id,
        parties=[
            CaseParty(
                key=party.party_key,
                name=party.name,
                role=party.role,
                party_type=party.party_type,
                document_id=party.document_id,
                status=party.status,
                is_original_party=party.is_original_party,
                metadata=dict(party.party_metadata or {}),
            )
            for party in parties
        ],
        representatives=[
            PartyRepresentative(
                represented_party_key=representative.represented_party_key,
                representative_party_key=representative.representative_party_key,
                representation_type=representative.representation_type,
                status=representative.status,
                started_at=representative.started_at,
                ended_at=representative.ended_at,
                metadata=dict(representative.representative_metadata or {}),
            )
            for representative in representatives
        ],
        relationships=[
            PartyRelationship(
                source_party_key=relationship.source_party_key,
                target_party_key=relationship.target_party_key,
                relationship_type=relationship.relationship_type,
                status=relationship.status,
                started_at=relationship.started_at,
                ended_at=relationship.ended_at,
                metadata=dict(relationship.relationship_metadata or {}),
            )
            for relationship in relationships
        ],
        events=[
            PartyEvent(
                event_type=event.event_type,
                title=event.title,
                description=event.description,
                occurred_on=event.occurred_on,
                party_keys=event.party_keys or [],
                metadata=dict(event.event_metadata or {}),
            )
            for event in events
        ],
        metadata=dict(state.state_metadata or {}),
    )


def _build_state_detail_payload(
    db: Session,
    state: CasePartyStateModel,
) -> dict:
    parties, representatives, relationships, events = _load_state_bundle(db, state)

    return {
        "id": state.id,
        "tenant_id": state.tenant_id,
        "case_id": state.case_id,
        "area": state.area,
        "state_metadata": state.state_metadata or {},
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "parties": [
            {
                "id": party.id,
                "tenant_id": party.tenant_id,
                "party_state_id": party.party_state_id,
                "party_key": party.party_key,
                "name": party.name,
                "role": party.role,
                "party_type": party.party_type,
                "document_id": party.document_id,
                "status": party.status,
                "is_original_party": party.is_original_party,
                "party_metadata": party.party_metadata or {},
                "created_at": party.created_at,
                "updated_at": party.updated_at,
            }
            for party in parties
        ],
        "representatives": [
            {
                "id": representative.id,
                "tenant_id": representative.tenant_id,
                "party_state_id": representative.party_state_id,
                "represented_party_key": representative.represented_party_key,
                "representative_party_key": representative.representative_party_key,
                "representation_type": representative.representation_type,
                "status": representative.status,
                "started_at": representative.started_at,
                "ended_at": representative.ended_at,
                "representative_metadata": representative.representative_metadata or {},
                "created_at": representative.created_at,
            }
            for representative in representatives
        ],
        "relationships": [
            {
                "id": relationship.id,
                "tenant_id": relationship.tenant_id,
                "party_state_id": relationship.party_state_id,
                "source_party_key": relationship.source_party_key,
                "target_party_key": relationship.target_party_key,
                "relationship_type": relationship.relationship_type,
                "status": relationship.status,
                "started_at": relationship.started_at,
                "ended_at": relationship.ended_at,
                "relationship_metadata": relationship.relationship_metadata or {},
                "created_at": relationship.created_at,
            }
            for relationship in relationships
        ],
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "title": event.title,
                "description": event.description,
                "occurred_on": event.occurred_on,
                "party_keys": event.party_keys or [],
                "event_metadata": event.event_metadata or {},
                "created_at": event.created_at,
            }
            for event in events
        ],
    }


def _touch_state(db: Session, state_id: int) -> None:
    db.query(CasePartyStateModel).filter(CasePartyStateModel.id == state_id).update(
        {"updated_at": func.now()},
        synchronize_session=False,
    )


@router.post(
    "",
    response_model=CasePartyStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_case_party_state(
    payload: CasePartyStateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == payload.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    existing_state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == current_user["tenant_id"],
            CasePartyStateModel.case_id == payload.case_id,
        )
        .first()
    )
    if existing_state:
        raise HTTPException(status_code=409, detail="Case party state already exists")

    state = CasePartyStateModel(
        tenant_id=current_user["tenant_id"],
        case_id=payload.case_id,
        area=payload.area,
        state_metadata=payload.metadata,
    )
    db.add(state)
    db.flush()

    for party in payload.parties:
        db.add(
            CasePartyModel(
                tenant_id=current_user["tenant_id"],
                party_state_id=state.id,
                party_key=party.key,
                name=party.name,
                role=party.role,
                party_type=party.party_type,
                document_id=party.document_id,
                status=party.status,
                is_original_party=party.is_original_party,
                party_metadata=party.metadata,
            )
        )

    db.add(
        CasePartyEventModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            event_type="initial_party_state_created",
            title="Estado inicial de partes criado",
            description="Estrutura persistida inicial do caso.",
            occurred_on=None,
            party_keys=[party.key for party in payload.parties],
            event_metadata={
                **payload.metadata,
                "source": "api_create_case_party_state",
            },
        )
    )

    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.get(
    "/case/{case_id}",
    response_model=list[CasePartyStateOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_case_party_states_for_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == current_user["tenant_id"],
            CasePartyStateModel.case_id == case_id,
        )
        .order_by(CasePartyStateModel.updated_at.desc())
        .all()
    )


@router.get(
    "/{state_id}",
    response_model=CasePartyStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_case_party_state(
    state_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    return _build_state_detail_payload(db, state)


@router.post(
    "/{state_id}/representatives",
    response_model=CasePartyStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def add_case_party_representative(
    state_id: int,
    payload: PartyRepresentativeIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    parties, representatives, relationships, events = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        parties,
        representatives,
        relationships,
        events,
    )

    updated_state = service.add_representative(
        domain_state,
        PartyRepresentative(
            represented_party_key=payload.represented_party_key,
            representative_party_key=payload.representative_party_key,
            representation_type=payload.representation_type,
            status=payload.status,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            metadata=payload.metadata,
        ),
        occurred_on=payload.started_at,
    )
    event = updated_state.events[-1]

    db.add(
        CasePartyRepresentativeModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            represented_party_key=payload.represented_party_key,
            representative_party_key=payload.representative_party_key,
            representation_type=payload.representation_type,
            status=payload.status,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            representative_metadata=payload.metadata,
        )
    )
    db.add(
        CasePartyEventModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            occurred_on=event.occurred_on,
            party_keys=event.party_keys,
            event_metadata=event.metadata,
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.post(
    "/{state_id}/relationships",
    response_model=CasePartyStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def add_case_party_relationship(
    state_id: int,
    payload: PartyRelationshipIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    parties, representatives, relationships, events = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        parties,
        representatives,
        relationships,
        events,
    )

    updated_state = service.add_relationship(
        domain_state,
        PartyRelationship(
            source_party_key=payload.source_party_key,
            target_party_key=payload.target_party_key,
            relationship_type=payload.relationship_type,
            status=payload.status,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            metadata=payload.metadata,
        ),
        occurred_on=payload.started_at,
    )
    event = updated_state.events[-1]

    db.add(
        CasePartyRelationshipModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            source_party_key=payload.source_party_key,
            target_party_key=payload.target_party_key,
            relationship_type=payload.relationship_type,
            status=payload.status,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            relationship_metadata=payload.metadata,
        )
    )
    db.add(
        CasePartyEventModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            occurred_on=event.occurred_on,
            party_keys=event.party_keys,
            event_metadata=event.metadata,
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.post(
    "/{state_id}/status",
    response_model=CasePartyStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def update_case_party_status(
    state_id: int,
    payload: PartyStatusUpdateIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    parties, representatives, relationships, events = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        parties,
        representatives,
        relationships,
        events,
    )

    updated_state = service.update_party_status(
        domain_state,
        party_key=payload.party_key,
        status=payload.status,
        title=payload.title,
        description=payload.description,
        occurred_on=payload.occurred_on,
        metadata=payload.metadata,
    )
    event = updated_state.events[-1]
    updated_party = next(
        party for party in updated_state.parties if party.key == payload.party_key
    )

    party_model = (
        db.query(CasePartyModel)
        .filter(
            CasePartyModel.tenant_id == current_user["tenant_id"],
            CasePartyModel.party_state_id == state.id,
            CasePartyModel.party_key == payload.party_key,
        )
        .first()
    )
    if not party_model:
        raise HTTPException(status_code=404, detail="Party not found")

    party_model.status = updated_party.status
    party_model.party_metadata = dict(updated_party.metadata or {})
    db.add(party_model)

    db.add(
        CasePartyEventModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            occurred_on=event.occurred_on,
            party_keys=event.party_keys,
            event_metadata=event.metadata,
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.post(
    "/{state_id}/succession",
    response_model=CasePartyStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def register_case_party_succession(
    state_id: int,
    payload: RegisterSuccessionIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    parties, representatives, relationships, events = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        parties,
        representatives,
        relationships,
        events,
    )

    updated_state = service.register_succession(
        domain_state,
        original_party_key=payload.original_party_key,
        successor_party=CaseParty(
            key=payload.successor_party.key,
            name=payload.successor_party.name,
            role=payload.successor_party.role,
            party_type=payload.successor_party.party_type,
            document_id=payload.successor_party.document_id,
            status=payload.successor_party.status,
            is_original_party=payload.successor_party.is_original_party,
            metadata=payload.successor_party.metadata,
        ),
        relationship_type=payload.relationship_type,
        occurred_on=payload.occurred_on,
        description=payload.description,
    )
    event = updated_state.events[-1]
    relationship = updated_state.relationships[-1]
    original_party = next(
        party for party in updated_state.parties if party.key == payload.original_party_key
    )
    successor_party = next(
        party for party in updated_state.parties if party.key == payload.successor_party.key
    )

    original_party_model = (
        db.query(CasePartyModel)
        .filter(
            CasePartyModel.tenant_id == current_user["tenant_id"],
            CasePartyModel.party_state_id == state.id,
            CasePartyModel.party_key == payload.original_party_key,
        )
        .first()
    )
    if not original_party_model:
        raise HTTPException(status_code=404, detail="Original party not found")

    original_party_model.status = original_party.status
    original_party_model.party_metadata = dict(original_party.metadata or {})
    db.add(original_party_model)

    db.add(
        CasePartyModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            party_key=successor_party.key,
            name=successor_party.name,
            role=successor_party.role,
            party_type=successor_party.party_type,
            document_id=successor_party.document_id,
            status=successor_party.status,
            is_original_party=successor_party.is_original_party,
            party_metadata=successor_party.metadata,
        )
    )
    db.add(
        CasePartyRelationshipModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            source_party_key=relationship.source_party_key,
            target_party_key=relationship.target_party_key,
            relationship_type=relationship.relationship_type,
            status=relationship.status,
            started_at=relationship.started_at,
            ended_at=relationship.ended_at,
            relationship_metadata=relationship.metadata,
        )
    )
    db.add(
        CasePartyEventModel(
            tenant_id=current_user["tenant_id"],
            party_state_id=state.id,
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            occurred_on=event.occurred_on,
            party_keys=event.party_keys,
            event_metadata=event.metadata,
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.get(
    "/{state_id}/snapshot",
    response_model=DocumentPartySnapshotOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_case_party_snapshot(
    state_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    parties, representatives, relationships, events = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        parties,
        representatives,
        relationships,
        events,
    )
    snapshot = service.build_document_snapshot(domain_state)

    def _party_payload(party: CaseParty) -> dict:
        party_model = next(
            persisted_party
            for persisted_party in parties
            if persisted_party.party_key == party.key
        )
        return {
            "id": party_model.id,
            "tenant_id": party_model.tenant_id,
            "party_state_id": party_model.party_state_id,
            "party_key": party_model.party_key,
            "name": party_model.name,
            "role": party_model.role,
            "party_type": party_model.party_type,
            "document_id": party_model.document_id,
            "status": party_model.status,
            "is_original_party": party_model.is_original_party,
            "party_metadata": party_model.party_metadata or {},
            "created_at": party_model.created_at,
            "updated_at": party_model.updated_at,
        }

    def _representative_payload(representative: PartyRepresentative) -> dict:
        representative_model = next(
            persisted_representative
            for persisted_representative in representatives
            if persisted_representative.represented_party_key == representative.represented_party_key
            and persisted_representative.representative_party_key == representative.representative_party_key
            and persisted_representative.representation_type == representative.representation_type
        )
        return {
            "id": representative_model.id,
            "tenant_id": representative_model.tenant_id,
            "party_state_id": representative_model.party_state_id,
            "represented_party_key": representative_model.represented_party_key,
            "representative_party_key": representative_model.representative_party_key,
            "representation_type": representative_model.representation_type,
            "status": representative_model.status,
            "started_at": representative_model.started_at,
            "ended_at": representative_model.ended_at,
            "representative_metadata": representative_model.representative_metadata or {},
            "created_at": representative_model.created_at,
        }

    def _relationship_payload(relationship: PartyRelationship) -> dict:
        relationship_model = next(
            persisted_relationship
            for persisted_relationship in relationships
            if persisted_relationship.source_party_key == relationship.source_party_key
            and persisted_relationship.target_party_key == relationship.target_party_key
            and persisted_relationship.relationship_type == relationship.relationship_type
        )
        return {
            "id": relationship_model.id,
            "tenant_id": relationship_model.tenant_id,
            "party_state_id": relationship_model.party_state_id,
            "source_party_key": relationship_model.source_party_key,
            "target_party_key": relationship_model.target_party_key,
            "relationship_type": relationship_model.relationship_type,
            "status": relationship_model.status,
            "started_at": relationship_model.started_at,
            "ended_at": relationship_model.ended_at,
            "relationship_metadata": relationship_model.relationship_metadata or {},
            "created_at": relationship_model.created_at,
        }

    return {
        "active_parties": [_party_payload(party) for party in snapshot.active_parties],
        "historical_parties": [_party_payload(party) for party in snapshot.historical_parties],
        "representatives": [
            _representative_payload(representative)
            for representative in snapshot.representatives
        ],
        "succession_relationships": [
            _relationship_payload(relationship)
            for relationship in snapshot.succession_relationships
        ],
        "events": [
            {
                "id": event_model.id,
                "event_type": event_model.event_type,
                "title": event_model.title,
                "description": event_model.description,
                "occurred_on": event_model.occurred_on,
                "party_keys": event_model.party_keys or [],
                "event_metadata": event_model.event_metadata or {},
                "created_at": event_model.created_at,
            }
            for event_model in events
        ],
        "metadata": snapshot.metadata,
    }
