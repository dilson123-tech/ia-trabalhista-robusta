import datetime as dt

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



def _case_context_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _case_context_unique(items):
    result = []
    seen = set()
    for item in items or []:
        text = _case_context_text(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _case_context_attr(obj, *names, default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None and value != "":
                return value
    return default


def _case_context_filter(query, model, attr_name, value):
    column = getattr(model, attr_name, None)
    if column is not None:
        return query.filter(column == value)
    return query


def _case_context_order(query, model):
    order_col = getattr(model, "created_at", None)
    if order_col is None:
        order_col = getattr(model, "updated_at", None)
    if order_col is not None:
        return query.order_by(order_col.desc())
    return query


def _case_context_rows(query, limit=30):
    try:
        return query.limit(limit).all()
    except Exception:
        return []


def _build_case_operational_context(db: Session, case: Case, current_user):
    """
    Monta contexto operacional estruturado do caso usando apenas dados já cadastrados.
    Não lê PDF inteiro, não faz OCR, não cria migration e não promete resultado judicial.
    """
    tenant_id = current_user["tenant_id"]

    try:
        from app.models.case_attachment import CaseAttachment
    except Exception:
        CaseAttachment = None

    try:
        from app.models.case_evidence_checklist import CaseEvidenceChecklistItem
    except Exception:
        CaseEvidenceChecklistItem = None

    try:
        from app.models.case_party_state import CasePartyModel, CasePartyStateModel
    except Exception:
        CasePartyModel = None
        CasePartyStateModel = None

    title = _case_context_text(getattr(case, "title", ""))
    description = _case_context_text(getattr(case, "description", ""))
    legal_area = _case_context_text(getattr(case, "legal_area", ""))
    action_type = _case_context_text(getattr(case, "action_type", ""))

    haystack = f"{title} {description} {legal_area} {action_type}".lower()

    def has(*markers):
        return any(marker in haystack for marker in markers)

    facts = []
    if has("semi-reboque", "semirreboque", "carreta", "implemento rodoviário", "implemento rodoviario"):
        facts.append("Discussão sobre locação, uso, guarda ou devolução de semi-reboque/carreta.")
    if has("contrato de locação", "locação de semi", "locacao de semi", "locação", "locacao"):
        facts.append("Necessidade de conferir contrato de locação e obrigações assumidas pelas partes.")
    if has("primeira parcela", "1ª parcela", "1a parcela"):
        facts.append("Narrativa indica pagamento apenas da primeira parcela.")
    if has("demais parcelas", "inadimplência", "inadimplencia", "ausência de pagamento", "ausencia de pagamento"):
        facts.append("Narrativa indica discussão sobre inadimplência das parcelas posteriores.")
    if has("não devolução", "nao devolucao", "não devolvido", "nao devolvido", "não devolveu", "nao devolveu"):
        facts.append("Narrativa envolve alegação de não devolução do bem.")
    if has("indenização", "indenizacao", "perdas e danos", "valor do equipamento", "valor do bem"):
        facts.append("Pedido indenizatório depende de prova do dano, valor do bem e nexo causal.")
    if has("lucros cessantes"):
        facts.append("Lucros cessantes exigem prova específica, não apenas presunção genérica.")
    if has("verbas acessórias", "verbas acessorias", "multa", "juros", "correção", "correcao"):
        facts.append("Verbas acessórias dependem de base contratual, cálculo e atualização.")

    if not facts and (legal_area or action_type):
        facts.append(
            f"Contexto jurídico informado: área {legal_area or 'não informada'}"
            f" / tipo {action_type or 'não informado'}."
        )

    attachments = []
    if CaseAttachment is not None:
        q = db.query(CaseAttachment)
        q = _case_context_filter(q, CaseAttachment, "tenant_id", tenant_id)
        q = _case_context_filter(q, CaseAttachment, "case_id", case.id)
        q = _case_context_order(q, CaseAttachment)
        for row in _case_context_rows(q, limit=20):
            filename = _case_context_text(
                _case_context_attr(
                    row,
                    "filename",
                    "original_filename",
                    "stored_filename",
                    "file_name",
                    "name",
                    default="Arquivo sem nome",
                )
            )
            attachments.append(
                {
                    "filename": filename,
                    "category": _case_context_text(
                        _case_context_attr(row, "category", "file_category", "document_type", "mime_type", default="")
                    ),
                    "description": _case_context_text(
                        _case_context_attr(row, "description", "notes", "summary", default="")
                    ),
                }
            )

    checklist_items = []
    validated_count = 0
    pending_count = 0
    if CaseEvidenceChecklistItem is not None:
        q = db.query(CaseEvidenceChecklistItem)
        q = _case_context_filter(q, CaseEvidenceChecklistItem, "tenant_id", tenant_id)
        q = _case_context_filter(q, CaseEvidenceChecklistItem, "case_id", case.id)
        q = _case_context_order(q, CaseEvidenceChecklistItem)
        for row in _case_context_rows(q, limit=50):
            label = _case_context_text(
                _case_context_attr(row, "title", "description", "item", "name", default="Item de checklist")
            )
            status_raw = _case_context_attr(row, "status", "state", default="")
            status = _case_context_text(status_raw) or "sem status"
            is_validated = bool(
                _case_context_attr(row, "validated", "is_validated", "done", "is_done", default=False)
            )
            status_lower = status.lower()
            if is_validated or status_lower in {"validado", "validated", "done", "concluído", "concluido"}:
                validated_count += 1
            elif status_lower in {"pendente", "pending", "open", "aberto"}:
                pending_count += 1
            checklist_items.append({"title": label, "status": status})

    witnesses = []
    if CasePartyStateModel is not None and CasePartyModel is not None:
        state_query = db.query(CasePartyStateModel)
        state_query = _case_context_filter(state_query, CasePartyStateModel, "tenant_id", tenant_id)
        state_query = _case_context_filter(state_query, CasePartyStateModel, "case_id", case.id)
        state_query = _case_context_order(state_query, CasePartyStateModel)
        states = _case_context_rows(state_query, limit=10)

        for state in states:
            party_query = db.query(CasePartyModel)
            party_query = _case_context_filter(party_query, CasePartyModel, "state_id", getattr(state, "id", None))
            party_query = _case_context_order(party_query, CasePartyModel)
            for party in _case_context_rows(party_query, limit=50):
                role = _case_context_text(_case_context_attr(party, "role", "type", "party_type", default=""))
                name = _case_context_text(_case_context_attr(party, "name", "full_name", default=""))
                knowledge = _case_context_text(
                    _case_context_attr(
                        party,
                        "what_knows",
                        "knowledge",
                        "description",
                        "notes",
                        "statement",
                        "summary",
                        default="",
                    )
                )

                role_lower = role.lower()
                knowledge_lower = knowledge.lower()
                if not any(
                    marker in f"{role_lower} {knowledge_lower}"
                    for marker in ("testemunha", "depoente", "condutor", "motorista", "witness")
                ):
                    continue

                witnesses.append(
                    {
                        "name": name or "Pessoa sem nome informado",
                        "role": role or "testemunha/depoente",
                        "knowledge": knowledge,
                    }
                )

    attachments = attachments[:10]
    checklist_items = checklist_items[:15]
    witnesses = witnesses[:10]

    summary_parts = []
    summary_parts.extend(facts[:6])

    if attachments:
        filenames = ", ".join(item["filename"] for item in attachments[:4] if item.get("filename"))
        if filenames:
            summary_parts.append(f"Anexo(s) cadastrado(s): {filenames}.")
    if checklist_items:
        total = len(checklist_items)
        summary_parts.append(f"Checklist de provas: {validated_count}/{total} item(ns) validados.")
    if witnesses:
        witness_names = ", ".join(
            f'{item["name"]} ({item["role"]})' for item in witnesses[:4] if item.get("name")
        )
        if witness_names:
            summary_parts.append(f"Testemunha(s)/depoente(s): {witness_names}.")

    summary = " ".join(_case_context_unique(summary_parts)).strip()

    return {
        "facts": _case_context_unique(facts),
        "attachments": attachments,
        "checklist": {
            "total": len(checklist_items),
            "validated": validated_count,
            "pending": pending_count,
            "items": checklist_items,
        },
        "witnesses": witnesses,
        "summary": summary,
    }


def _strip_existing_case_context_from_summary(value: str) -> str:
    text = _case_context_text(value)
    marker = "Contexto específico considerado:"
    if marker not in text:
        return text
    return text.split(marker, 1)[0].strip()


def _is_generated_case_context_step(value: str) -> bool:
    text = _case_context_text(value).lower()
    generated_prefixes = (
        "revisar anexo(s) cadastrado(s) no caso:",
        "conferir checklist probatório:",
        "preparar perguntas objetivas para testemunha(s)/depoente(s):",
        "transformar os fatos-chave estruturados em linha do tempo antes de gerar peça pronta.",
    )
    return any(text.startswith(prefix) for prefix in generated_prefixes)


def _enrich_analysis_with_case_context(analysis, case_context):
    enriched = dict(analysis or {})
    if not isinstance(case_context, dict):
        return enriched

    facts = case_context.get("facts") or []
    summary = _case_context_text(case_context.get("summary"))
    attachments = case_context.get("attachments") or []
    checklist = case_context.get("checklist") or {}
    witnesses = case_context.get("witnesses") or []

    if not (facts or attachments or checklist.get("total") or witnesses or summary):
        return enriched

    enriched["case_context"] = case_context
    enriched["case_context_facts"] = facts
    enriched["case_context_summary"] = summary

    base_summary = _strip_existing_case_context_from_summary(enriched.get("summary"))
    if summary:
        enriched["summary"] = (
            f"{base_summary} Contexto específico considerado: {summary}".strip()
            if base_summary
            else f"Contexto específico considerado: {summary}"
        )
    else:
        enriched["summary"] = base_summary

    issues = list(enriched.get("issues") or [])
    next_steps = [
        step
        for step in list(enriched.get("next_steps") or [])
        if not _is_generated_case_context_step(step)
    ]

    facts_joined = " ".join(facts).lower()

    if "locação" in facts_joined or "locacao" in facts_joined:
        issues.append("Verificar contrato de locação, obrigações assumidas, vigência, multas, entrega e devolução do bem.")
    if "não devolução" in facts_joined or "nao devolucao" in facts_joined:
        issues.append("Confrontar alegação de não devolução do bem com documentos, termos, comunicações e depoimentos disponíveis.")
    if "indenizatório" in facts_joined or "indenizatorio" in facts_joined or "valor do bem" in facts_joined:
        issues.append("Validar prova do valor indenizatório do equipamento e separar dano efetivo de verbas acessórias.")
    if "lucros cessantes" in facts_joined:
        issues.append("Exigir demonstração específica dos lucros cessantes, com base documental e cálculo verificável.")
    if attachments:
        issues.append("Usar os anexos cadastrados como base de conferência documental antes de qualquer peça.")
    if checklist.get("total"):
        issues.append("Cruzar análise jurídica com o checklist de provas e pendências já cadastrado.")
    if witnesses:
        issues.append("Explorar depoimento das testemunhas/depoentes sobre uso, guarda, entrega/devolução e responsabilidade operacional.")

    if attachments:
        filenames = ", ".join(item.get("filename", "") for item in attachments[:3] if item.get("filename"))
        next_steps.append(f"Revisar anexo(s) cadastrado(s) no caso: {filenames}.")
    if checklist.get("total"):
        next_steps.append(
            f"Conferir checklist probatório: {checklist.get('validated', 0)}/{checklist.get('total', 0)} item(ns) validados."
        )
    if witnesses:
        names = ", ".join(item.get("name", "") for item in witnesses[:3] if item.get("name"))
        next_steps.append(f"Preparar perguntas objetivas para testemunha(s)/depoente(s): {names}.")
    if facts:
        next_steps.append("Transformar os fatos-chave estruturados em linha do tempo antes de gerar peça pronta.")

    enriched["issues"] = _case_context_unique(issues)
    enriched["next_steps"] = _case_context_unique(next_steps)

    return enriched


def _enrich_case_analysis_record_with_case_context(db: Session, record: CaseAnalysis, case: Case, current_user):
    if not record:
        return record

    case_context = _build_case_operational_context(db=db, case=case, current_user=current_user)
    full_analysis = dict(record.analysis or {})
    technical = full_analysis.get("technical", {})
    if not isinstance(technical, dict):
        technical = {}

    enriched_technical = _enrich_analysis_with_case_context(technical, case_context)
    full_analysis["technical"] = enriched_technical

    executive_data = dict(record.executive_data or {})
    viability = executive_data.get("viability") or full_analysis.get("viability") or {}
    strategic = executive_data.get("strategic") or full_analysis.get("strategic") or {}
    decision_seed = executive_data.get("decision") or full_analysis.get("decision") or {}

    if isinstance(viability, dict) and isinstance(decision_seed, dict):
        decision = generate_executive_summary(enriched_technical, viability, decision_seed)
        full_analysis["decision"] = decision
        executive_data["decision"] = decision

    full_analysis["strategic"] = strategic
    full_analysis["viability"] = viability
    executive_data["viability"] = viability
    executive_data["strategic"] = strategic

    record.risk_level = enriched_technical.get("risk_level", "medium")
    record.summary = enriched_technical.get("summary", "")
    record.issues = enriched_technical.get("issues", [])
    record.next_steps = enriched_technical.get("next_steps", [])
    record.analysis = full_analysis
    record.executive_data = executive_data

    db.add(record)
    db.commit()
    db.refresh(record)
    return record

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
    payload_data = payload.model_dump()
    if payload_data.get("client_whatsapp_consent") and not payload_data.get("client_whatsapp_consent_at"):
        payload_data["client_whatsapp_consent_at"] = dt.datetime.now(dt.UTC)

    case = Case(
        tenant_id=current_user["tenant_id"],
        **payload_data,
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
        "client_name": getattr(case, "client_name", None),
        "client_whatsapp": getattr(case, "client_whatsapp", None),
        "client_whatsapp_consent": getattr(case, "client_whatsapp_consent", False),
        "client_whatsapp_consent_at": getattr(case, "client_whatsapp_consent_at", None),
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
        existing_analysis = _enrich_case_analysis_record_with_case_context(
            db=db,
            record=existing_analysis,
            case=case,
            current_user=current_user,
        )
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
    analysis_record = _enrich_case_analysis_record_with_case_context(
        db=db,
        record=analysis_record,
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
    analysis_record = _enrich_case_analysis_record_with_case_context(
        db=db,
        record=analysis_record,
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
    analysis_record = _enrich_case_analysis_record_with_case_context(
        db=db,
        record=analysis_record,
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

        case_context = _build_case_operational_context(
            db=db,
            case=case,
            current_user=current_user,
        )
        analysis_data = _enrich_analysis_with_case_context(analysis_data, case_context)

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
