from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Case, CaseAnalysis
from app.schemas import CaseCreate, CaseOut
from app.core.security import require_role, require_auth
from app.services import analyze_case
from app.core.tenant import scoped_query


router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


@router.get(
    "",
    response_model=list[CaseOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_cases(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    return (
        scoped_query(db, Case, current_user)
        .order_by(Case.created_at.desc())
        .all()
    )
@router.post(
    "",
    response_model=CaseOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    # Idempotente por case_number: se já existir, só devolve
    existing = db.query(Case).filter(Case.case_number == payload.case_number, Case.tenant_id == current_user["tenant_id"]).first()
    if existing:
        return existing

    # Pydantic v2: usar model_dump() em vez de dict()
    case = Case(
        tenant_id=current_user["tenant_id"],
        **payload.model_dump(),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get(
    "/{case_id}",
    response_model=CaseOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
@router.get(
    "/{case_id}/analysis",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def analyze_case_endpoint(
    case_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    
    # Verifica se já existe análise para esse case + tenant (idempotência)
    existing_analysis = (
        db.query(CaseAnalysis)
        .filter(
            CaseAnalysis.case_id == case.id,
            CaseAnalysis.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if existing_analysis:
        return {
            "case_id": case.id,
            "analysis_id": existing_analysis.id,
            "analysis": existing_analysis.analysis,
        }

    analysis = analyze_case(
        case_number=case.case_number,
        title=case.title,
        description=case.description,
    )

    record = CaseAnalysis(
        tenant_id=current_user["tenant_id"],
        case_id=case.id,
        risk_level=analysis.get("risk_level", "medium"),
        summary=analysis.get("summary", ""),
        issues=analysis.get("issues", []),
        next_steps=analysis.get("next_steps", []),
        analysis=analysis,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "case_id": case.id,
        "analysis_id": record.id,
        "analysis": analysis,
    }

