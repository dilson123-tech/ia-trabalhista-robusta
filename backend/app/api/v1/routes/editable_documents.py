from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case, User
from app.api.v1.routes.cases import _get_or_create_case_analysis_record
from app.models.editable_document import EditableDocument, EditableDocumentVersion
from app.schemas.editable_document import (
    EditableDocumentCreate,
    EditableDocumentDetailOut,
    EditableDocumentOut,
    EditableDocumentVersionCreate,
    EditableDocumentVersionOut,
)
from app.services.editor_export_service import build_editor_html, generate_editor_pdf
from app.services.analysis_foundations import build_analysis_foundations

router = APIRouter(
    prefix="/editable-documents",
    tags=["editable-documents"],
)


def _resolve_current_user_id(db: Session, current_user: dict) -> int | None:
    username = current_user.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user.id if user else None


def _build_document_detail_payload(
    db: Session,
    document: EditableDocument,
) -> dict:
    versions = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.tenant_id == document.tenant_id,
            EditableDocumentVersion.editable_document_id == document.id,
        )
        .order_by(EditableDocumentVersion.version_number.asc())
        .all()
    )

    return {
        "id": document.id,
        "tenant_id": document.tenant_id,
        "case_id": document.case_id,
        "created_by_user_id": document.created_by_user_id,
        "area": document.area,
        "document_type": document.document_type,
        "title": document.title,
        "status": document.status,
        "current_version_number": document.current_version_number,
        "document_metadata": document.document_metadata or {},
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "versions": [
            {
                "id": version.id,
                "editable_document_id": version.editable_document_id,
                "tenant_id": version.tenant_id,
                "version_number": version.version_number,
                "approved": version.approved,
                "notes": version.notes,
                "sections": version.sections or [],
                "version_metadata": version.version_metadata or {},
                "created_by_user_id": version.created_by_user_id,
                "created_at": version.created_at,
            }
            for version in versions
        ],
    }


def _safe_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        item_text = str(item).strip()
        if item_text:
            items.append(item_text)
    return items


def _paragraphs(lines: list[str]) -> str:
    clean_lines: list[str] = []
    seen: set[str] = set()

    for line in lines:
        normalized = _safe_text(line)
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        clean_lines.append(normalized)

    return "\n\n".join(clean_lines)


def _build_missing_context_items(
    case_description: str,
    technical_summary: str,
    issues: list[str],
    next_steps: list[str],
) -> list[str]:
    missing: list[str] = []

    if len(case_description) < 80:
        missing.append(
            "detalhar fatos, período, jornada, pedidos pretendidos e provas disponíveis no cadastro do caso"
        )
    if not technical_summary:
        missing.append("executar ou complementar a análise técnica do caso")
    if not issues:
        missing.append("explicitar controvérsias jurídicas e pontos críticos")
    if not next_steps:
        missing.append("registrar diligências, documentos e próximos passos relevantes")

    return missing


def _build_insufficient_content(block_title: str, missing_items: list[str]) -> str:
    block_guidance = {
        "Resumo Fático": [
            "Faltam elementos para narrar os fatos com segurança.",
            "Complete datas, período, jornada, contexto do conflito e provas disponíveis para este bloco.",
        ],
        "Fundamentação": [
            "Faltam elementos para sustentar a tese jurídica com segurança.",
            "Complete controvérsia principal, violação legal, enquadramento jurídico e estratégia para este bloco.",
        ],
        "Pedidos": [
            "Faltam elementos para estruturar os pedidos com segurança.",
            "Complete pretensões principais, verbas buscadas, reflexos e requerimentos finais para este bloco.",
        ],
    }

    guidance = block_guidance.get(
        block_title,
        [
            "Faltam elementos para montar este bloco com segurança.",
            "Complete o caso com informações materiais e estratégicas antes de gerar a peça assistida.",
        ],
    )

    base = [
        f"Dados insuficientes para montar automaticamente o bloco '{block_title}' com segurança.",
        guidance[0],
        guidance[1],
    ]

    if missing_items:
        base.append("Pendências mínimas identificadas:")
        base.extend([f"- {item}" for item in missing_items])

    return "\n".join(base)

def _build_assisted_sections(case: Case, analysis_record) -> list[dict]:
    full_analysis = analysis_record.analysis or {}
    executive_data = analysis_record.executive_data or {}

    technical = full_analysis.get("technical", {}) if isinstance(full_analysis, dict) else {}
    strategic = full_analysis.get("strategic", {}) if isinstance(full_analysis, dict) else {}
    viability = executive_data.get("viability") or (
        full_analysis.get("viability", {}) if isinstance(full_analysis, dict) else {}
    )
    decision = executive_data.get("decision") or (
        full_analysis.get("decision", {}) if isinstance(full_analysis, dict) else {}
    )

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

    normative_basis = _string_list(foundations.get("normative_basis") if isinstance(foundations, dict) else [])
    factual_elements = _string_list(foundations.get("factual_elements_considered") if isinstance(foundations, dict) else [])
    probative_gaps = _string_list(foundations.get("probative_gaps") if isinstance(foundations, dict) else [])

    case_description = _safe_text(case.description)
    technical_summary = _safe_text(technical.get("summary") if isinstance(technical, dict) else "")
    issues = _string_list(technical.get("issues") if isinstance(technical, dict) else [])
    next_steps = _string_list(technical.get("next_steps") if isinstance(technical, dict) else [])
    recommended_strategy = _safe_text(
        strategic.get("recommended_strategy") if isinstance(strategic, dict) else ""
    )
    critical_points = _string_list(
        strategic.get("critical_points") if isinstance(strategic, dict) else []
    )
    viability_recommendation = _safe_text(
        viability.get("recommendation") if isinstance(viability, dict) else ""
    )
    executive_summary = _safe_text(
        decision.get("executive_summary") if isinstance(decision, dict) else ""
    )
    final_status = _safe_text(decision.get("final_status") if isinstance(decision, dict) else "")

    missing_items = _build_missing_context_items(
        case_description=case_description,
        technical_summary=technical_summary,
        issues=issues,
        next_steps=next_steps,
    )

    insufficient_context = len(case_description) < 80 and (
        not technical_summary
        or "apenas identificador" in f"{case_description} {technical_summary}".lower()
        or "dados insuficientes" in f"{case_description} {technical_summary}".lower()
    )

    if insufficient_context:
        return [
            {
                "key": "resumo_fatico",
                "title": "Resumo Fático",
                "content": _build_insufficient_content("Resumo Fático", missing_items),
                "source": "assisted_draft",
                "status": "draft",
                "metadata": {
                    "origin_sources": ["case", "technical_analysis"],
                    "generation_mode": "assisted_draft_from_analysis",
                    "guardrail_status": "insufficient_data",
                },
            },
            {
                "key": "fundamentacao",
                "title": "Fundamentação",
                "content": _build_insufficient_content("Fundamentação", missing_items),
                "source": "assisted_draft",
                "status": "draft",
                "metadata": {
                    "origin_sources": ["technical_analysis", "strategic_analysis", "viability"],
                    "generation_mode": "assisted_draft_from_analysis",
                    "guardrail_status": "insufficient_data",
                },
            },
            {
                "key": "pedidos",
                "title": "Pedidos",
                "content": _build_insufficient_content("Pedidos", missing_items),
                "source": "assisted_draft",
                "status": "draft",
                "metadata": {
                    "origin_sources": ["decision", "viability", "technical_analysis"],
                    "generation_mode": "assisted_draft_from_analysis",
                    "guardrail_status": "insufficient_data",
                },
            },
        ]

    resumo_fatico = _paragraphs(
        [
            f"Trata-se do caso {case.case_number} — {case.title}.",
            case_description,
            (
                "A narrativa fática acima deverá ser revisada e completada, na versão final, com datas, períodos, jornadas, documentos e demais elementos concretos já disponíveis no caso."
                if len(case_description) < 220
                else ""
            ),
        ]
    )

    fundamentacao = _paragraphs(
        [
            "À luz do quadro fático narrado, a fundamentação deve enfrentar a controvérsia jurídica central do caso com base nos fatos já descritos e na prova disponível.",
            (
                "A base normativa preliminar identificada para sustentar a tese envolve: "
                + "; ".join(normative_basis)
                + "."
                if normative_basis
                else ""
            ),
            (
                "Na leitura atual do caso, foram considerados os seguintes elementos fáticos relevantes: "
                + "; ".join(factual_elements)
                + "."
                if factual_elements
                else ""
            ),
            (
                "Antes do fechamento da tese, permanecem lacunas probatórias que exigem saneamento: "
                + "; ".join(probative_gaps)
                + "."
                if probative_gaps
                else ""
            ),
            (
                f"A linha argumentativa preliminar indicada para a peça consiste em {recommended_strategy}."
                if recommended_strategy
                else ""
            ),
            (
                "Devem ser enfrentados, de forma articulada, os seguintes pontos controvertidos: "
                + "; ".join(issues)
                + "."
                if issues
                else ""
            ),
            (
                "Na construção da tese, merecem destaque os seguintes pontos críticos: "
                + "; ".join(critical_points)
                + "."
                if critical_points
                else ""
            ),
            (
                f"Como orientação de coerência interna da minuta, considera-se a síntese executiva já consolidada: {executive_summary}"
                if executive_summary
                else ""
            ),
            (
                f"A redação final deve observar a seguinte prudência jurídica já indicada na análise de viabilidade: {viability_recommendation}"
                if viability_recommendation
                else ""
            ),
        ]
    )

    pedidos = _paragraphs(
        [
            "Ao final, requer-se a procedência dos pedidos compatíveis com os fatos narrados, a tese sustentada e a prova atualmente disponível.",
            (
                "Em linha preliminar, a minuta pode concentrar os pedidos nos seguintes eixos materiais já identificados no caso: "
                + "; ".join(issues)
                + "."
                if issues
                else ""
            ),
            "Também devem ser avaliados, conforme o caso concreto, reflexos legais, consectários, requerimentos probatórios e demais pedidos acessórios pertinentes.",
            (
                f"O fechamento dos pedidos deve respeitar a conclusão provisória registrada na análise: {final_status}."
                if final_status
                else ""
            ),
            (
                "Antes do fechamento definitivo, conferir e completar os seguintes pontos: "
                + "; ".join(next_steps)
                + "."
                if next_steps
                else "Antes da versão final, revisar pedidos principais, reflexos, acessórios e requerimentos probatórios conforme a prova disponível."
            ),
        ]
    )

    return [
        {
            "key": "resumo_fatico",
            "title": "Resumo Fático",
            "content": resumo_fatico,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "technical_analysis"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "fundamentacao",
            "title": "Fundamentação",
            "content": fundamentacao,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["technical_analysis", "strategic_analysis", "viability", "decision"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "pedidos",
            "title": "Pedidos",
            "content": pedidos,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["decision", "viability", "technical_analysis"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
    ]


@router.post(
    "",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_editable_document(
    payload: EditableDocumentCreate,
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

    current_user_id = _resolve_current_user_id(db, current_user)

    document = EditableDocument(
        tenant_id=current_user["tenant_id"],
        case_id=payload.case_id,
        created_by_user_id=current_user_id,
        area=payload.area,
        document_type=payload.document_type,
        title=payload.title,
        status="draft",
        current_version_number=1,
        document_metadata=payload.metadata,
    )
    db.add(document)
    db.flush()

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=1,
        approved=False,
        notes=payload.notes,
        sections=[section.model_dump() for section in payload.sections],
        version_metadata={
            **payload.metadata,
            "source": "api_create_editable_document",
        },
    )
    db.add(version)
    db.commit()
    db.refresh(document)

    return _build_document_detail_payload(db, document)


@router.get(
    "/case/{case_id}",
    response_model=list[EditableDocumentOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_editable_documents_for_case(
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
        db.query(EditableDocument)
        .filter(
            EditableDocument.tenant_id == current_user["tenant_id"],
            EditableDocument.case_id == case_id,
        )
        .order_by(EditableDocument.updated_at.desc())
        .all()
    )


@router.get(
    "/{document_id}",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_editable_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    return _build_document_detail_payload(db, document)


@router.delete(
    "/{document_id}",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_editable_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    versions_count = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
        )
        .count()
    )

    db.delete(document)
    db.commit()

    return {
        "deleted_document_id": document_id,
        "deleted_versions_count": versions_count,
        "detail": "Editable document deleted successfully",
    }


@router.get(
    "/{document_id}/export/html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def export_editable_document_html(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    approved_version = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .first()
    )

    if not approved_version:
        raise HTTPException(
            status_code=409,
            detail="Editable document does not have an approved version for final export",
        )

    html = build_editor_html(
        {
            "title": document.title,
            "area": document.area,
            "document_type": document.document_type,
        },
        {
            "version_number": approved_version.version_number,
            "sections": approved_version.sections or [],
        },
    )

    return HTMLResponse(content=html)


@router.get(
    "/{document_id}/export/pdf",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def export_editable_document_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    approved_version = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .first()
    )

    if not approved_version:
        raise HTTPException(
            status_code=409,
            detail="Editable document does not have an approved version for final export",
        )

    html = build_editor_html(
        {
            "title": document.title,
            "area": document.area,
            "document_type": document.document_type,
        },
        {
            "version_number": approved_version.version_number,
            "sections": approved_version.sections or [],
        },
    )

    pdf_bytes = generate_editor_pdf(html)

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="editable_document_{document.id}_v{approved_version.version_number}.pdf"'
        },
    )



@router.post(
    "/{document_id}/generate-assisted-draft",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def generate_assisted_draft(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == document.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Archived cases cannot generate assisted draft",
        )

    analysis_record = _get_or_create_case_analysis_record(db=db, case=case, current_user=current_user)
    assisted_sections = _build_assisted_sections(case, analysis_record)

    current_user_id = _resolve_current_user_id(db, current_user)
    next_version_number = document.current_version_number + 1

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=next_version_number,
        approved=False,
        notes="Versão assistida gerada a partir da análise do caso",
        sections=assisted_sections,
        version_metadata={
            "source": "assisted_draft_from_analysis",
            "analysis_id": analysis_record.id,
            "case_id": case.id,
            "origin_modules": [
                "analysis",
                "executive_summary",
                "executive_decision",
                "analysis_foundations",
            ],
        },
    )
    db.add(version)

    document.current_version_number = next_version_number
    document.status = "draft"
    document.document_metadata = {
        **(document.document_metadata or {}),
        "last_generation_mode": "assisted_draft_from_analysis",
    }
    db.add(document)

    db.commit()
    db.refresh(document)

    return _build_document_detail_payload(db, document)


@router.post(
    "/{document_id}/versions",
    response_model=EditableDocumentVersionOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_editable_document_version(
    document_id: int,
    payload: EditableDocumentVersionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    current_user_id = _resolve_current_user_id(db, current_user)
    next_version_number = document.current_version_number + 1

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=next_version_number,
        approved=payload.approved,
        notes=payload.notes,
        sections=[section.model_dump() for section in payload.sections],
        version_metadata=payload.metadata,
    )
    db.add(version)

    document.current_version_number = next_version_number
    document.status = "approved" if payload.approved else "draft"
    db.add(document)

    db.commit()
    db.refresh(version)

    return version
