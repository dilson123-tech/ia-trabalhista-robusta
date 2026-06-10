from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case
from app.models.case_timeline import CaseTimelineItem
from app.schemas.case_timeline import (
    CaseTimelineCreate,
    CaseTimelineOut,
    CaseTimelineUpdate,
)


router = APIRouter(
    prefix="/cases/{case_id}/timeline",
    tags=["case-timeline"],
)


def _get_case_or_404(db: Session, current_user, case_id: int) -> Case:
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get(
    "",
    response_model=list[CaseTimelineOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    return (
        db.query(CaseTimelineItem)
        .filter(
            CaseTimelineItem.tenant_id == current_user["tenant_id"],
            CaseTimelineItem.case_id == case_id,
        )
        .order_by(
            CaseTimelineItem.sort_order.asc(),
            CaseTimelineItem.created_at.asc(),
            CaseTimelineItem.id.asc(),
        )
        .all()
    )


@router.post(
    "",
    response_model=CaseTimelineOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_case_timeline_item(
    case_id: int,
    payload: CaseTimelineCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    record = CaseTimelineItem(
        tenant_id=current_user["tenant_id"],
        case_id=case_id,
        event_date=(payload.event_date or "").strip() or None,
        title=payload.title.strip(),
        description=payload.description.strip(),
        related_evidence=(payload.related_evidence or "").strip() or None,
        related_witness=(payload.related_witness or "").strip() or None,
        pending_note=(payload.pending_note or "").strip() or None,
        sort_order=payload.sort_order,
        timeline_metadata=dict(payload.metadata or {}),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.patch(
    "/{item_id}",
    response_model=CaseTimelineOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def update_case_timeline_item(
    case_id: int,
    item_id: int,
    payload: CaseTimelineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    record = (
        db.query(CaseTimelineItem)
        .filter(
            CaseTimelineItem.id == item_id,
            CaseTimelineItem.case_id == case_id,
            CaseTimelineItem.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Timeline item not found")

    if payload.event_date is not None:
        record.event_date = payload.event_date.strip() or None
    if payload.title is not None:
        record.title = payload.title.strip()
    if payload.description is not None:
        record.description = payload.description.strip()
    if payload.related_evidence is not None:
        record.related_evidence = payload.related_evidence.strip() or None
    if payload.related_witness is not None:
        record.related_witness = payload.related_witness.strip() or None
    if payload.pending_note is not None:
        record.pending_note = payload.pending_note.strip() or None
    if payload.sort_order is not None:
        record.sort_order = payload.sort_order

    if payload.metadata:
        metadata = dict(record.timeline_metadata or {})
        metadata.update(payload.metadata)
        record.timeline_metadata = metadata

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.delete(
    "/{item_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_case_timeline_item(
    case_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    record = (
        db.query(CaseTimelineItem)
        .filter(
            CaseTimelineItem.id == item_id,
            CaseTimelineItem.case_id == case_id,
            CaseTimelineItem.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Timeline item not found")

    db.delete(record)
    db.commit()

    return None
