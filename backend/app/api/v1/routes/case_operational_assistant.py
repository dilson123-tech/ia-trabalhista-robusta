from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case
from app.schemas.case_operational_assistant import (
    CaseOperationalAssistantRequest,
    CaseOperationalAssistantResponse,
)
from app.services.case_operational_assistant import build_case_operational_assistant_response


router = APIRouter(
    prefix="/cases/{case_id}/operational-assistant",
    tags=["case-operational-assistant"],
)


def _get_case_or_404(db: Session, current_user, case_id: int) -> Case:
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post(
    "",
    response_model=CaseOperationalAssistantResponse,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def ask_case_operational_assistant(
    case_id: int,
    payload: CaseOperationalAssistantRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = _get_case_or_404(db, current_user, case_id)

    return build_case_operational_assistant_response(
        db=db,
        case=case,
        current_user=current_user,
        message=payload.message,
    )
