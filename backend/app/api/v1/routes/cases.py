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
from app.services.analysis_foundations import build_analysis_foundations
from app.services import analyze_case
from app.services.usage import register_usage
from app.services.plan_enforcement import enforce_plan_limits, PlanAction
router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


def _get_or_create_case_analysis_record(
    db: Session,
    case: Case,
    current_user,
):
    analysis_record = (
        db.query(CaseAnalysis)
        .filter(
            CaseAnalysis.case_id == case.id,
            CaseAnalysis.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if analysis_record:
        return analysis_record

    enforce_plan_limits(db, current_user["tenant_id"], PlanAction.AI_ANALYSIS_CREATE)

    analysis = analyze_case(

          case_number=case.case_number,

          title=case.title,

          description=case.description,

          legal_area=getattr(case, "legal_area", None),

          action_type=getattr(case, "action_type", None),

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

    analysis_record = CaseAnalysis(
        tenant_id=current_user["tenant_id"],
        case_id=case.id,
        risk_level=analysis.get("risk_level", "medium"),
        summary=analysis.get("summary", ""),
        issues=analysis.get("issues", []),
        next_steps=analysis.get("next_steps", []),
        analysis=full_analysis,
        executive_data=executive_data,
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    return analysis_record



def _ensure_case_not_archived(case: Case):
    if getattr(case, "status", None) == "archived":
        raise HTTPException(
            status_code=409,
            detail="Archived cases cannot run analysis or executive actions",
        )


_PUBLIC_ANALYSIS_FORBIDDEN_KEYS = {
    "score",
    "probability",
    "probability_percent",
    "success_probability",
    "confidence_level",
}


def _sanitize_public_analysis_payload(payload):
    """
    Remove métricas numéricas de prognóstico das respostas públicas da API.

    Regra de produto:
    - interno/banco/motor: pode manter score/probabilidade para cálculo;
    - API pública/frontend/PDF/peça: não deve expor score, probabilidade,
      confidence_level ou equivalentes como previsão de resultado judicial.
    """
    if isinstance(payload, dict):
        sanitized = {}
        for key, value in payload.items():
            if str(key).lower() in _PUBLIC_ANALYSIS_FORBIDDEN_KEYS:
                continue
            sanitized[key] = _sanitize_public_analysis_payload(value)
        return sanitized

    if isinstance(payload, list):
        return [_sanitize_public_analysis_payload(item) for item in payload]

    return payload


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
        "legal_area": getattr(case, "legal_area", None),
        "action_type": getattr(case, "action_type", None),
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

    previous_status = getattr(case, "status", None)
    next_status = payload.status

    if previous_status == "archived" and next_status != "archived":
        enforce_plan_limits(db, current_user["tenant_id"], PlanAction.CASE_RESTORE)

    case.status = next_status
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
    force: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
):
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    _ensure_case_not_archived(case)

    # Verifica se já existe análise para esse case + tenant (idempotência)
    existing_analysis = (
        db.query(CaseAnalysis)
        .filter(
            CaseAnalysis.case_id == case.id,
            CaseAnalysis.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if existing_analysis and not force:
        return {
            "case_id": case.id,
            "analysis_id": existing_analysis.id,
            "analysis": _sanitize_public_analysis_payload(existing_analysis.analysis),
            "source": "cache",
        }

    if existing_analysis and force:
        db.delete(existing_analysis)
        db.commit()

    enforce_plan_limits(db, current_user["tenant_id"], PlanAction.AI_ANALYSIS_CREATE)

    analysis = analyze_case(

          case_number=case.case_number,

          title=case.title,

          description=case.description,

          legal_area=getattr(case, "legal_area", None),

          action_type=getattr(case, "action_type", None),

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
        "analysis": _sanitize_public_analysis_payload(record.analysis),
        "source": "fresh",
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
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    _ensure_case_not_archived(case)

    analysis_record = _get_or_create_case_analysis_record(
        db=db,
        case=case,
        current_user=current_user,
    )

    full_analysis = analysis_record.analysis or {}
    executive_data = analysis_record.executive_data or {}

    technical = full_analysis.get("technical", {})
    viability = executive_data.get("viability") or full_analysis.get("viability", {})
    decision = executive_data.get("decision") or full_analysis.get("decision", {})

    html = generate_report_html(
        case={
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
        },
        analysis=technical,
        viability=viability,
        executive_decision=decision,
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

    _ensure_case_not_archived(case)

    analysis_record = _get_or_create_case_analysis_record(
        db=db,
        case=case,
        current_user=current_user,
    )

    full_analysis = analysis_record.analysis or {}
    executive_data = analysis_record.executive_data or {}

    technical = full_analysis.get("technical", {})
    strategic = full_analysis.get("strategic", {})
    viability = executive_data.get("viability") or full_analysis.get("viability", {})
    decision = executive_data.get("decision") or full_analysis.get("decision", {})

    foundations = build_analysis_foundations(
        case={
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "legal_area": getattr(case, "legal_area", None),
            "action_type": getattr(case, "action_type", None),
        },
        technical=technical,
        viability=viability,
        decision=decision,
    )

    return {
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
        },
        "technical_analysis": _sanitize_public_analysis_payload(technical),
        "strategic_analysis": _sanitize_public_analysis_payload(strategic),
        "viability": _sanitize_public_analysis_payload(viability),
        "executive_decision": _sanitize_public_analysis_payload(decision),
        "analysis_foundations": foundations,
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

    _ensure_case_not_archived(case)

    analysis_record = _get_or_create_case_analysis_record(
        db=db,
        case=case,
        current_user=current_user,
    )

    full_analysis = analysis_record.analysis or {}
    executive_data = analysis_record.executive_data or {}

    technical = full_analysis.get("technical", {})
    viability = executive_data.get("viability") or full_analysis.get("viability", {})
    decision = executive_data.get("decision") or full_analysis.get("decision", {})

    foundations = build_analysis_foundations(
        case={
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "legal_area": getattr(case, "legal_area", None),
            "action_type": getattr(case, "action_type", None),
        },
        technical=technical,
        viability=viability,
        decision=decision,
    )

    html = generate_report_html(
        case={
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
        },
        analysis=technical,
        viability=viability,
        executive_decision=decision,
    )

    return {
        "case_id": case.id,
        "executive_decision": _sanitize_public_analysis_payload(decision),
        "analysis_foundations": foundations,
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

    _ensure_case_not_archived(case)

    analysis = (
        scoped_query(db, CaseAnalysis, current_user)
        .filter(CaseAnalysis.case_id == case.id)
        .order_by(CaseAnalysis.created_at.desc())
        .first()
    )


    def _build_executive_payload():
        stored_analysis = analysis.analysis if analysis and isinstance(analysis.analysis, dict) else {}
        analysis_data = stored_analysis.get("technical", {}) if isinstance(stored_analysis, dict) else {}

        if not isinstance(analysis_data, dict) or not analysis_data.get("summary"):
            analysis_data = {
                "summary": analysis.summary if analysis else "",
                "risk_level": analysis.risk_level if analysis else "medium",
                "issues": analysis.issues if analysis else [],
                "next_steps": analysis.next_steps if analysis else [],
            }

        if not isinstance(analysis_data, dict) or not analysis_data.get("summary"):
            analysis_data = analyze_case(
                case_number=case.case_number,
                title=case.title,
                description=case.description,
                legal_area=getattr(case, "legal_area", None),
                action_type=getattr(case, "action_type", None),
            )

        existing_exec = analysis.executive_data if analysis and isinstance(analysis.executive_data, dict) else {}
        existing_viability = existing_exec.get("viability", {}) if isinstance(existing_exec, dict) else {}
        existing_strategic = existing_exec.get("strategic", {}) if isinstance(existing_exec, dict) else {}
        existing_decision = existing_exec.get("decision", {}) if isinstance(existing_exec, dict) else {}

        viability = existing_viability if (
            isinstance(existing_viability, dict)
            and existing_viability.get("probability") is not None
            and existing_viability.get("score") is not None
        ) else calculate_viability(analysis_data)

        strategic = existing_strategic if (
            isinstance(existing_strategic, dict)
            and existing_strategic.get("financial_risk")
        ) else strategic_diagnosis(analysis_data)

        decision_seed = generate_decision(analysis_data, viability)
        if isinstance(existing_decision, dict):
            decision_seed = {**existing_decision, **decision_seed}

        decision = generate_executive_summary(analysis_data, viability, decision_seed)
        return analysis_data, strategic, viability, decision

    executive_data = analysis.executive_data if analysis else {}
    decision_data = executive_data.get("decision", {}) if isinstance(executive_data, dict) else {}
    strategic_data = executive_data.get("strategic", {}) if isinstance(executive_data, dict) else {}
    viability_data = executive_data.get("viability", {}) if isinstance(executive_data, dict) else {}

    insufficient_payload = (
        isinstance(viability_data, dict)
        and isinstance(decision_data, dict)
        and isinstance(strategic_data, dict)
        and (viability_data.get("dimensions") or {}).get("insufficient_data") is True
        and decision_data.get("final_status") == "DADOS INSUFICIENTES"
        and decision_data.get("probability_percent") is None
    )

    needs_refresh = (
        not analysis
        or not isinstance(executive_data, dict)
        or not isinstance(decision_data, dict)
        or not isinstance(strategic_data, dict)
        or not isinstance(viability_data, dict)
        or not decision_data.get("executive_summary")
        or (
            decision_data.get("probability_percent") is None
            and not insufficient_payload
        )
        or (
            not strategic_data.get("financial_risk")
            and not insufficient_payload
        )
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

    if needs_refresh:
        executive_payload = {
            "viability": viability,
            "decision": decision,
            "strategic": strategic,
            "technical": analysis_data,
        }
    else:
        executive_payload = dict(analysis.executive_data or {})
        technical_payload = {}
        if isinstance(analysis.analysis, dict):
            technical_payload = analysis.analysis.get("technical", {}) or {}
        executive_payload["technical"] = technical_payload

    pdf_bytes = generate_executive_pdf(
        case_data={
            "case_number": case.case_number,
            "title": case.title,
        },
        executive_data=executive_payload,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=executive_case_{case.id}.pdf"},
    )
