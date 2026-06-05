from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case, CaseContactLog
from app.schemas.case_contact_log import CaseContactLogCreate, CaseContactLogOut


router = APIRouter(
    prefix="/cases/{case_id}/contact-logs",
    tags=["case-contact-logs"],
)


def _get_case_or_404(db: Session, current_user, case_id: int) -> Case:
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _current_user_id(current_user) -> int | None:
    for key in ("user_id", "id", "sub"):
        value = current_user.get(key) if isinstance(current_user, dict) else None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


@router.get(
    "",
    response_model=list[CaseContactLogOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_case_contact_logs(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    return (
        db.query(CaseContactLog)
        .filter(
            CaseContactLog.tenant_id == current_user["tenant_id"],
            CaseContactLog.case_id == case_id,
        )
        .order_by(CaseContactLog.occurred_at.desc(), CaseContactLog.created_at.desc())
        .all()
    )


@router.post(
    "",
    response_model=CaseContactLogOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_case_contact_log(
    case_id: int,
    payload: CaseContactLogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = _get_case_or_404(db, current_user, case_id)

    occurred_at = payload.occurred_at or dt.datetime.now(dt.UTC)

    record = CaseContactLog(
        tenant_id=current_user["tenant_id"],
        case_id=case.id,
        contact_type=payload.contact_type,
        direction=payload.direction,
        summary=payload.summary.strip(),
        note=payload.note.strip() if payload.note else None,
        occurred_at=occurred_at,
        created_by_user_id=_current_user_id(current_user),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record



@router.delete(
    "/{log_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_case_contact_log(
    case_id: int,
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    record = (
        db.query(CaseContactLog)
        .filter(
            CaseContactLog.tenant_id == current_user["tenant_id"],
            CaseContactLog.case_id == case_id,
            CaseContactLog.id == log_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Contact log not found")

    db.delete(record)
    db.commit()
    return None
