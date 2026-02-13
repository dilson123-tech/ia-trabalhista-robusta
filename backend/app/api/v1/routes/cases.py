from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Case, CaseAnalysis
from app.schemas import CaseCreate, CaseOut
from app.core.security import require_role
from app.services import analyze_case
from app.services.case_analysis import list_case_analyses
from app.schemas.case_analysis import CaseAnalysisOut


router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


@router.get(
    "",
    response_model=list[CaseOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_cases(db: Session = Depends(get_db)):
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.post(
    "",
    response_model=CaseOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    # Pydantic v2: usar model_dump() em vez de dict()
    case = Case(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get(
    "/{case_id}",
    response_model=CaseOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get(
    "/{case_id}/analysis",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def analyze_case_endpoint(case_id: int, db: Session = Depends(get_db)):
    """
    Endpoint D07:
    - Busca o caso
    - Roda análise baseada em regras
    - Persiste histórico em case_analyses
    - Retorna a análise + metadados básicos
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    analysis = analyze_case(
        case_number=case.case_number,
        title=case.title,
        description=case.description,
    )

    # hardening: garante issues como dict (schema espera dict; evita [] quebrar response_model)
    issues = analysis.get("issues")
    if issues is None:
        analysis["issues"] = {}
    elif isinstance(issues, list):
        analysis["issues"] = {"items": issues}
    elif not isinstance(issues, dict):
        analysis["issues"] = {"value": issues}

    record = CaseAnalysis(
        case_id=case.id,
        risk_level=analysis["risk_level"],
        summary=analysis["summary"],
        issues=analysis["issues"],
        next_steps=analysis["next_steps"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "case_id": case.id,
        "analysis_id": record.id,
        "created_at": record.created_at,
        "analysis": analysis,
    }

@router.get(
    "/{case_id}/analysis/history",
    response_model=list[CaseAnalysisOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_case_analysis_history(
    case_id: int,
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """Retorna o histórico de análises já realizadas para um caso."""
    return list_case_analyses(db=db, case_id=case_id, limit=limit)

