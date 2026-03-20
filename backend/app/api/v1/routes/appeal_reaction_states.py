from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case
from app.models.appeal_reaction_state import (
    AppealDeadlineModel,
    AppealDecisionPointModel,
    AppealDraftRefModel,
    AppealReactionStateModel,
    AppealStrategyItemModel,
)
from app.modules.appeals_reactions.contracts import (
    AppealDeadline,
    AppealDraftRef,
    AppealReactionState,
    AppealStrategyItem,
    DecisionPoint,
    JudicialDecision,
)
from app.modules.appeals_reactions.service import AppealsReactionsService
from app.schemas.appeal_reaction_state import (
    AppealDeadlineIn,
    AppealDraftRefIn,
    AppealReactionStateCreate,
    AppealReactionStateDetailOut,
    AppealReactionStateOut,
    AppealReactionSummaryOut,
    AppealStrategyItemIn,
)

router = APIRouter(
    prefix="/appeal-reaction-states",
    tags=["appeal-reaction-states"],
)

service = AppealsReactionsService()


def _get_state_or_404(
    db: Session,
    *,
    state_id: int,
    tenant_id: int,
) -> AppealReactionStateModel:
    state = (
        db.query(AppealReactionStateModel)
        .filter(
            AppealReactionStateModel.id == state_id,
            AppealReactionStateModel.tenant_id == tenant_id,
        )
        .first()
    )
    if not state:
        raise HTTPException(status_code=404, detail="Appeal reaction state not found")
    return state


def _load_state_bundle(
    db: Session,
    state: AppealReactionStateModel,
) -> tuple[
    list[AppealDecisionPointModel],
    list[AppealDeadlineModel],
    list[AppealStrategyItemModel],
    list[AppealDraftRefModel],
]:
    decision_points = (
        db.query(AppealDecisionPointModel)
        .filter(
            AppealDecisionPointModel.tenant_id == state.tenant_id,
            AppealDecisionPointModel.appeal_reaction_state_id == state.id,
        )
        .order_by(AppealDecisionPointModel.id.asc())
        .all()
    )
    deadlines = (
        db.query(AppealDeadlineModel)
        .filter(
            AppealDeadlineModel.tenant_id == state.tenant_id,
            AppealDeadlineModel.appeal_reaction_state_id == state.id,
        )
        .order_by(AppealDeadlineModel.id.asc())
        .all()
    )
    strategy_items = (
        db.query(AppealStrategyItemModel)
        .filter(
            AppealStrategyItemModel.tenant_id == state.tenant_id,
            AppealStrategyItemModel.appeal_reaction_state_id == state.id,
        )
        .order_by(AppealStrategyItemModel.id.asc())
        .all()
    )
    appeal_drafts = (
        db.query(AppealDraftRefModel)
        .filter(
            AppealDraftRefModel.tenant_id == state.tenant_id,
            AppealDraftRefModel.appeal_reaction_state_id == state.id,
        )
        .order_by(AppealDraftRefModel.id.asc())
        .all()
    )
    return decision_points, deadlines, strategy_items, appeal_drafts


def _build_domain_state(
    state: AppealReactionStateModel,
    decision_points: list[AppealDecisionPointModel],
    deadlines: list[AppealDeadlineModel],
    strategy_items: list[AppealStrategyItemModel],
    appeal_drafts: list[AppealDraftRefModel],
) -> AppealReactionState:
    decision = JudicialDecision(
        area=state.area,
        case_id=state.case_id,
        tenant_id=state.tenant_id,
        decision_type=state.decision_type,
        title=state.decision_title,
        summary=state.decision_summary,
        decision_date=state.decision_date,
        unfavorable_points=[
            DecisionPoint(
                key=point.point_key,
                title=point.title,
                description=point.description,
                outcome=point.outcome,
                legal_effect=point.legal_effect,
                metadata=dict(point.point_metadata or {}),
            )
            for point in decision_points
        ],
        metadata=dict(state.decision_metadata or {}),
    )

    return AppealReactionState(
        area=state.area,
        case_id=state.case_id,
        tenant_id=state.tenant_id,
        source_decision=decision,
        deadlines=[
            AppealDeadline(
                key=deadline.deadline_key,
                title=deadline.title,
                due_date=deadline.due_date,
                status=deadline.status,
                metadata=dict(deadline.deadline_metadata or {}),
            )
            for deadline in deadlines
        ],
        strategy_items=[
            AppealStrategyItem(
                key=item.strategy_key,
                title=item.title,
                description=item.description,
                target_point_keys=item.target_point_keys or [],
                priority=item.priority,
                metadata=dict(item.strategy_metadata or {}),
            )
            for item in strategy_items
        ],
        appeal_drafts=[
            AppealDraftRef(
                document_type=draft.document_type,
                title=draft.title,
                status=draft.status,
                version=draft.version,
                metadata=dict(draft.draft_metadata or {}),
            )
            for draft in appeal_drafts
        ],
        metadata=dict(state.state_metadata or {}),
    )


def _build_state_detail_payload(
    db: Session,
    state: AppealReactionStateModel,
) -> dict:
    decision_points, deadlines, strategy_items, appeal_drafts = _load_state_bundle(db, state)

    return {
        "id": state.id,
        "tenant_id": state.tenant_id,
        "case_id": state.case_id,
        "area": state.area,
        "decision_type": state.decision_type,
        "decision_title": state.decision_title,
        "decision_summary": state.decision_summary,
        "decision_date": state.decision_date,
        "decision_metadata": state.decision_metadata or {},
        "state_metadata": state.state_metadata or {},
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "decision_points": [
            {
                "id": point.id,
                "tenant_id": point.tenant_id,
                "appeal_reaction_state_id": point.appeal_reaction_state_id,
                "point_key": point.point_key,
                "title": point.title,
                "description": point.description,
                "outcome": point.outcome,
                "legal_effect": point.legal_effect,
                "point_metadata": point.point_metadata or {},
                "created_at": point.created_at,
            }
            for point in decision_points
        ],
        "deadlines": [
            {
                "id": deadline.id,
                "tenant_id": deadline.tenant_id,
                "appeal_reaction_state_id": deadline.appeal_reaction_state_id,
                "deadline_key": deadline.deadline_key,
                "title": deadline.title,
                "due_date": deadline.due_date,
                "status": deadline.status,
                "deadline_metadata": deadline.deadline_metadata or {},
                "created_at": deadline.created_at,
            }
            for deadline in deadlines
        ],
        "strategy_items": [
            {
                "id": item.id,
                "tenant_id": item.tenant_id,
                "appeal_reaction_state_id": item.appeal_reaction_state_id,
                "strategy_key": item.strategy_key,
                "title": item.title,
                "description": item.description,
                "target_point_keys": item.target_point_keys or [],
                "priority": item.priority,
                "strategy_metadata": item.strategy_metadata or {},
                "created_at": item.created_at,
            }
            for item in strategy_items
        ],
        "appeal_drafts": [
            {
                "id": draft.id,
                "tenant_id": draft.tenant_id,
                "appeal_reaction_state_id": draft.appeal_reaction_state_id,
                "document_type": draft.document_type,
                "title": draft.title,
                "status": draft.status,
                "version": draft.version,
                "draft_metadata": draft.draft_metadata or {},
                "created_at": draft.created_at,
            }
            for draft in appeal_drafts
        ],
    }


def _touch_state(db: Session, state_id: int) -> None:
    db.query(AppealReactionStateModel).filter(
        AppealReactionStateModel.id == state_id
    ).update(
        {"updated_at": func.now()},
        synchronize_session=False,
    )


@router.post(
    "",
    response_model=AppealReactionStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_appeal_reaction_state(
    payload: AppealReactionStateCreate,
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

    state = AppealReactionStateModel(
        tenant_id=current_user["tenant_id"],
        case_id=payload.case_id,
        area=payload.area,
        decision_type=payload.source_decision.decision_type,
        decision_title=payload.source_decision.title,
        decision_summary=payload.source_decision.summary,
        decision_date=payload.source_decision.decision_date,
        decision_metadata=payload.source_decision.metadata,
        state_metadata=payload.metadata,
    )
    db.add(state)
    db.flush()

    for point in payload.source_decision.unfavorable_points:
        db.add(
            AppealDecisionPointModel(
                tenant_id=current_user["tenant_id"],
                appeal_reaction_state_id=state.id,
                point_key=point.key,
                title=point.title,
                description=point.description,
                outcome=point.outcome,
                legal_effect=point.legal_effect,
                point_metadata=point.metadata,
            )
        )

    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.get(
    "/case/{case_id}",
    response_model=list[AppealReactionStateOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_appeal_reaction_states_for_case(
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
        db.query(AppealReactionStateModel)
        .filter(
            AppealReactionStateModel.tenant_id == current_user["tenant_id"],
            AppealReactionStateModel.case_id == case_id,
        )
        .order_by(AppealReactionStateModel.updated_at.desc())
        .all()
    )


@router.get(
    "/{state_id}",
    response_model=AppealReactionStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_appeal_reaction_state(
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
    "/{state_id}/deadlines",
    response_model=AppealReactionStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def add_appeal_deadline(
    state_id: int,
    payload: AppealDeadlineIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    decision_points, deadlines, strategy_items, appeal_drafts = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        decision_points,
        deadlines,
        strategy_items,
        appeal_drafts,
    )

    updated_state = service.add_deadline(
        domain_state,
        AppealDeadline(
            key=payload.key,
            title=payload.title,
            due_date=payload.due_date,
            status=payload.status,
            metadata=payload.metadata,
        ),
    )
    added_deadline = updated_state.deadlines[-1]

    db.add(
        AppealDeadlineModel(
            tenant_id=current_user["tenant_id"],
            appeal_reaction_state_id=state.id,
            deadline_key=added_deadline.key,
            title=added_deadline.title,
            due_date=added_deadline.due_date,
            status=added_deadline.status,
            deadline_metadata=dict(added_deadline.metadata or {}),
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.post(
    "/{state_id}/strategy-items",
    response_model=AppealReactionStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def add_appeal_strategy_item(
    state_id: int,
    payload: AppealStrategyItemIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    decision_points, deadlines, strategy_items, appeal_drafts = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        decision_points,
        deadlines,
        strategy_items,
        appeal_drafts,
    )

    try:
        updated_state = service.add_strategy_item(
            domain_state,
            AppealStrategyItem(
                key=payload.key,
                title=payload.title,
                description=payload.description,
                target_point_keys=payload.target_point_keys,
                priority=payload.priority,
                metadata=payload.metadata,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    added_item = updated_state.strategy_items[-1]

    db.add(
        AppealStrategyItemModel(
            tenant_id=current_user["tenant_id"],
            appeal_reaction_state_id=state.id,
            strategy_key=added_item.key,
            title=added_item.title,
            description=added_item.description,
            target_point_keys=added_item.target_point_keys,
            priority=added_item.priority,
            strategy_metadata=dict(added_item.metadata or {}),
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.post(
    "/{state_id}/drafts",
    response_model=AppealReactionStateDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def add_appeal_draft_ref(
    state_id: int,
    payload: AppealDraftRefIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    decision_points, deadlines, strategy_items, appeal_drafts = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        decision_points,
        deadlines,
        strategy_items,
        appeal_drafts,
    )

    updated_state = service.add_appeal_draft(
        domain_state,
        AppealDraftRef(
            document_type=payload.document_type,
            title=payload.title,
            status=payload.status,
            version=payload.version,
            metadata=payload.metadata,
        ),
    )
    added_draft = updated_state.appeal_drafts[-1]

    db.add(
        AppealDraftRefModel(
            tenant_id=current_user["tenant_id"],
            appeal_reaction_state_id=state.id,
            document_type=added_draft.document_type,
            title=added_draft.title,
            status=added_draft.status,
            version=added_draft.version,
            draft_metadata=dict(added_draft.metadata or {}),
        )
    )
    _touch_state(db, state.id)
    db.commit()
    db.refresh(state)

    return _build_state_detail_payload(db, state)


@router.get(
    "/{state_id}/summary",
    response_model=AppealReactionSummaryOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_appeal_reaction_summary(
    state_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    state = _get_state_or_404(
        db,
        state_id=state_id,
        tenant_id=current_user["tenant_id"],
    )
    decision_points, deadlines, strategy_items, appeal_drafts = _load_state_bundle(db, state)
    domain_state = _build_domain_state(
        state,
        decision_points,
        deadlines,
        strategy_items,
        appeal_drafts,
    )
    return service.summarize_reaction(domain_state)
