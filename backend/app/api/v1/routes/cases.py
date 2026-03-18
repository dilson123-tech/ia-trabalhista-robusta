from fastapi.responses import Response
from fastapi import APIRouter, Depends, HTTPException
from app.services.viability_engine import calculate_viability
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Case, CaseAnalysis
from app.schemas.case import CaseCreate, CaseOut, CaseStatusUpdate, DemoCleanupOut
from app.core.security import require_role, require_auth
from app.core.tenant import scoped_query
from app.services.report_engine import generate_report_html
from app.services.strategic_diagnosis import strategic_diagnosis
from app.services.decision_engine import generate_decision
from app.services.pdf_executive import generate_executive_pdf
from app.services.executive_summary_engine import generate_executive_summary
from app.services import analyze_case
from app.services.usage import register_usage
from app.services.plan_enforcement import enforce_plan_limits, PlanAction
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

    enforce_plan_limits(db, current_user["tenant_id"], PlanAction.CASE_CREATE)

    # Pydantic v2: usar model_dump() em vez de dict()
    case = Case(
        tenant_id=current_user["tenant_id"],
        **payload.model_dump(),
    )
    db.add(case)
    db.flush()

    register_usage(db, current_user["tenant_id"], "case_created", case.id)

    db.commit()
    response_data = {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "tenant_id": case.tenant_id,
    }

    return response_data


@router.patch(
    "/{case_id}/status",
    response_model=CaseOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def update_case_status(
    case_id: int,
    payload: CaseStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = payload.status
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.post(
    "/cleanup-demo",
    response_model=DemoCleanupOut,
    dependencies=[Depends(require_role("admin"))],
)
def cleanup_demo_cases(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    demo_cases = (
        scoped_query(db, Case, current_user)
        .filter(Case.case_number.like("DEMO-%"))
        .all()
    )

    if not demo_cases:
        return {
            "deleted_cases": 0,
            "deleted_analyses": 0,
        }

    case_ids = [case.id for case in demo_cases]

    deleted_analyses = (
        db.query(CaseAnalysis)
        .filter(
            CaseAnalysis.tenant_id == current_user["tenant_id"],
            CaseAnalysis.case_id.in_(case_ids),
        )
        .delete(synchronize_session=False)
    )

    deleted_cases = (
        db.query(Case)
        .filter(
            Case.tenant_id == current_user["tenant_id"],
            Case.id.in_(case_ids),
        )
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "deleted_cases": deleted_cases,
        "deleted_analyses": deleted_analyses,
    }


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



    strategic = strategic_diagnosis(analysis)

    viability = calculate_viability(analysis)

    decision = generate_decision(analysis, viability)
    decision = generate_executive_summary(analysis, viability, decision)

    executive_data = {
        "viability": viability,
        "decision": decision,
        "strategic": strategic,
    }

    full_analysis = {
        "technical": analysis,
        "strategic": strategic,
        "viability": viability,
        "decision": decision,
    }



    record = CaseAnalysis(

        tenant_id=current_user["tenant_id"],

        case_id=case.id,

        risk_level=analysis.get("risk_level", "medium"),

        summary=analysis.get("summary", ""),

        issues=analysis.get("issues", []),

        next_steps=analysis.get("next_steps", []),

        analysis=full_analysis,

        executive_data=executive_data,

    )



    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "case_id": case.id,
        "analysis_id": record.id,
        "analysis": record.analysis,
        "viability": viability,
    }






@router.get(
    "/{case_id}/report",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def generate_case_report(
    case_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    # Busca case respeitando tenant
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Busca análise salva
    analysis_record = (
        db.query(CaseAnalysis)
        .filter(
            CaseAnalysis.case_id == case.id,
            CaseAnalysis.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if not analysis_record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    html = generate_report_html(
        case={
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
        },
        analysis=analysis_record.analysis,
        viability=calculate_viability(analysis_record.analysis),
    )

    return {"report_html": html}


@router.get("/{case_id}/executive-summary")
def get_executive_summary(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(
        Case.id == case_id
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    analysis = analyze_case(
        case_number=case.case_number,
        title=case.title,
        description=case.description,
    )

    strategic = strategic_diagnosis(analysis)
    viability = calculate_viability(analysis)
    decision = generate_decision(analysis, viability)
    decision = generate_executive_summary(analysis, viability, decision)

    return {
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
        },
        "technical_analysis": analysis,
        "strategic_analysis": strategic,
        "viability": viability,
        "executive_decision": decision,
    }

@router.get("/{case_id}/executive-report")
def get_executive_report(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(
        Case.id == case_id
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    analysis = analyze_case(
        case_number=case.case_number,
        title=case.title,
        description=case.description,
    )

    strategic = strategic_diagnosis(analysis)
    viability = calculate_viability(analysis)
    decision = generate_decision(analysis, viability)
    decision = generate_executive_summary(analysis, viability, decision)

    html = generate_report_html(
        case={
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
        },
        analysis=analysis,
        viability=viability,
        executive_decision=decision,
    )

    return {
        "case_id": case.id,
        "executive_decision": decision,
        "report_html": html,
    }


@router.get(
    "/{case_id}/executive-pdf",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def generate_executive_pdf_route(
    case_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case não encontrado")

    analysis = (
        scoped_query(db, CaseAnalysis, current_user)
        .filter(CaseAnalysis.case_id == case.id)
        .order_by(CaseAnalysis.created_at.desc())
        .first()
    )


    def _build_executive_payload():
        analysis_data = analyze_case(
            case_number=case.case_number,
            title=case.title,
            description=case.description,
        )

        strategic = strategic_diagnosis(analysis_data)
        viability = calculate_viability(analysis_data)
        decision = generate_decision(analysis_data, viability)
        decision = generate_executive_summary(analysis_data, viability, decision)
        return analysis_data, strategic, viability, decision

    executive_data = analysis.executive_data if analysis else {}
    decision_data = executive_data.get("decision", {}) if isinstance(executive_data, dict) else {}
    strategic_data = executive_data.get("strategic", {}) if isinstance(executive_data, dict) else {}

    needs_refresh = (
        not analysis
        or not isinstance(executive_data, dict)
        or not isinstance(decision_data, dict)
        or not isinstance(strategic_data, dict)
        or not decision_data.get("executive_summary")
        or decision_data.get("probability_percent") is None
        or not strategic_data.get("financial_risk")
    )

    if needs_refresh:
        if not analysis:
            enforce_plan_limits(db, current_user["tenant_id"], PlanAction.AI_ANALYSIS_CREATE)

        analysis_data, strategic, viability, decision = _build_executive_payload()

        payload_analysis = {
            "technical": analysis_data,
            "strategic": strategic,
            "viability": viability,
            "decision": decision,
        }
        payload_executive = {
            "viability": viability,
            "decision": decision,
            "strategic": strategic,
        }

        if analysis:
            analysis.risk_level = analysis_data.get("risk_level", "medium")
            analysis.summary = analysis_data.get("summary", "")
            analysis.issues = analysis_data.get("issues", [])
            analysis.next_steps = analysis_data.get("next_steps", [])
            analysis.analysis = payload_analysis
            analysis.executive_data = payload_executive
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
        else:
            record = CaseAnalysis(
                tenant_id=current_user["tenant_id"],
                case_id=case.id,
                risk_level=analysis_data.get("risk_level", "medium"),
                summary=analysis_data.get("summary", ""),
                issues=analysis_data.get("issues", []),
                next_steps=analysis_data.get("next_steps", []),
                analysis=payload_analysis,
                executive_data=payload_executive,
            )

            db.add(record)
            db.commit()
            db.refresh(record)
            analysis = record

    pdf_bytes = generate_executive_pdf(
        case_data={
            "case_number": case.case_number,
            "title": case.title,
        },
        executive_data=analysis.executive_data or {},
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=executive_case_{case.id}.pdf"},
    )
