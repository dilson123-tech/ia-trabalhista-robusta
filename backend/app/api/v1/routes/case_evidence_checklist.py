from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case, CaseAttachment
from app.models.case_evidence_checklist import CaseEvidenceChecklistItem
from app.schemas.case_evidence_checklist import (
    CaseEvidenceChecklistCreate,
    CaseEvidenceChecklistOut,
    CaseEvidenceChecklistUpdate,
)


router = APIRouter(
    prefix="/cases/{case_id}/evidence-checklist",
    tags=["case-evidence-checklist"],
)


_ALLOWED_STATUSES = {
    "pending",
    "requested",
    "received",
    "validated",
    "waived",
    "needs_review",
}


def _get_case_or_404(db: Session, current_user, case_id: int) -> Case:
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _normalize_item_key(title: str) -> str:
    normalized = title.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return (normalized[:80] or "evidence_item") + "_" + uuid.uuid4().hex[:8]


def _validate_attachment_if_present(
    db: Session,
    *,
    current_user,
    case_id: int,
    attachment_id: int | None,
) -> None:
    if attachment_id is None:
        return

    attachment = (
        db.query(CaseAttachment)
        .filter(
            CaseAttachment.id == attachment_id,
            CaseAttachment.case_id == case_id,
            CaseAttachment.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")


@router.get(
    "",
    response_model=list[CaseEvidenceChecklistOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_case_evidence_checklist(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    return (
        db.query(CaseEvidenceChecklistItem)
        .filter(
            CaseEvidenceChecklistItem.tenant_id == current_user["tenant_id"],
            CaseEvidenceChecklistItem.case_id == case_id,
        )
        .order_by(
            CaseEvidenceChecklistItem.created_at.desc(),
            CaseEvidenceChecklistItem.id.desc(),
        )
        .all()
    )


@router.post(
    "",
    response_model=CaseEvidenceChecklistOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_case_evidence_checklist_item(
    case_id: int,
    payload: CaseEvidenceChecklistCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)
    _validate_attachment_if_present(
        db,
        current_user=current_user,
        case_id=case_id,
        attachment_id=payload.attachment_id,
    )

    item_key = (payload.item_key or "").strip() or _normalize_item_key(payload.title)

    existing_item = (
        db.query(CaseEvidenceChecklistItem)
        .filter(
            CaseEvidenceChecklistItem.tenant_id == current_user["tenant_id"],
            CaseEvidenceChecklistItem.case_id == case_id,
            CaseEvidenceChecklistItem.item_key == item_key,
        )
        .first()
    )
    if existing_item:
        raise HTTPException(status_code=409, detail="Evidence checklist item already exists")

    record = CaseEvidenceChecklistItem(
        tenant_id=current_user["tenant_id"],
        case_id=case_id,
        attachment_id=payload.attachment_id,
        item_key=item_key,
        title=payload.title.strip(),
        category=payload.category,
        status=payload.status,
        priority=payload.priority,
        requested_from=payload.requested_from,
        due_date=payload.due_date,
        notes=payload.notes,
        checklist_metadata=dict(payload.metadata or {}),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.patch(
    "/{item_id}",
    response_model=CaseEvidenceChecklistOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def update_case_evidence_checklist_item(
    case_id: int,
    item_id: int,
    payload: CaseEvidenceChecklistUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    record = (
        db.query(CaseEvidenceChecklistItem)
        .filter(
            CaseEvidenceChecklistItem.id == item_id,
            CaseEvidenceChecklistItem.case_id == case_id,
            CaseEvidenceChecklistItem.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Evidence checklist item not found")

    if payload.attachment_id is not None:
        _validate_attachment_if_present(
            db,
            current_user=current_user,
            case_id=case_id,
            attachment_id=payload.attachment_id,
        )
        record.attachment_id = payload.attachment_id

    if payload.title is not None:
        record.title = payload.title.strip()
    if payload.category is not None:
        record.category = payload.category
    if payload.status is not None:
        if payload.status not in _ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail="Invalid evidence checklist status")
        record.status = payload.status
    if payload.priority is not None:
        record.priority = payload.priority
    if payload.requested_from is not None:
        record.requested_from = payload.requested_from
    if payload.due_date is not None:
        record.due_date = payload.due_date
    if payload.notes is not None:
        record.notes = payload.notes

    if payload.metadata:
        metadata = dict(record.checklist_metadata or {})
        metadata.update(payload.metadata)
        record.checklist_metadata = metadata

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.delete(
    "/{item_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_case_evidence_checklist_item(
    case_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    record = (
        db.query(CaseEvidenceChecklistItem)
        .filter(
            CaseEvidenceChecklistItem.id == item_id,
            CaseEvidenceChecklistItem.case_id == case_id,
            CaseEvidenceChecklistItem.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Evidence checklist item not found")

    db.delete(record)
    db.commit()

    return None
