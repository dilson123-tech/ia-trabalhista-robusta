import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case, User, CasePartyModel, CasePartyStateModel
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


# PATCH: editor_export_display_title_v1
def _resolve_editor_export_title(
    db: Session,
    document: EditableDocument,
    tenant_id: int,
) -> str:
    metadata = document.document_metadata or {}

    for key in ("display_title", "editor_title", "export_title", "case_title"):
        title = _safe_text(metadata.get(key))
        if title:
            return title

    case = (
        db.query(Case)
        .filter(
            Case.id == document.case_id,
            Case.tenant_id == tenant_id,
        )
        .first()
    )
    if case:
        case_title = _safe_text(case.title)
        if case_title:
            return case_title

    return _safe_text(document.title) or "Documento Jurídico"


# PATCH: editor_fgts_claim_values_v1
def _format_brl(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    raw = f"{rounded:,.2f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_decimal_value(value) -> Decimal | None:
    if value is None or value == "":
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        return Decimal(str(value))

    raw = str(value).strip()
    if not raw:
        return None

    cleaned = re.sub(r"[^0-9,.\-]", "", raw)
    if not cleaned:
        return None

    # Formato BR: 2.300,00
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        # Formato simples/US: 2300.00
        cleaned = cleaned

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_int_value(value) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value if value >= 0 else None

    match = re.search(r"\d+", str(value))
    if not match:
        return None

    parsed = int(match.group(0))
    return parsed if parsed >= 0 else None


def _metadata_first_value(metadata: dict, keys: list[str]):
    if not isinstance(metadata, dict):
        return None

    for key in keys:
        if key in metadata and metadata.get(key) not in (None, ""):
            return metadata.get(key)

    # fallback tolerante para metadados com nomes próximos
    lowered = {str(k).lower(): v for k, v in metadata.items()}
    for key in keys:
        normalized_key = key.lower()
        if normalized_key in lowered and lowered[normalized_key] not in (None, ""):
            return lowered[normalized_key]

    return None


def _case_combined_text(case, metadata: dict) -> str:
    chunks = [
        getattr(case, "case_number", "") or "",
        getattr(case, "title", "") or "",
        getattr(case, "description", "") or "",
        str(metadata or ""),
    ]
    return " ".join(chunks).lower()


def _extract_salary_from_text(text: str) -> Decimal | None:
    patterns = [
        r"sal[aá]rio(?:\s+mensal)?(?:\s+aproximad[ao])?\s*(?:de|:)?\s*r?\$?\s*([0-9][0-9\.\,]*)",
        r"remunera[cç][aã]o(?:\s+mensal)?(?:\s+aproximad[ao])?\s*(?:de|:)?\s*r?\$?\s*([0-9][0-9\.\,]*)",
        r"recebendo\s+remunera[cç][aã]o(?:\s+mensal)?(?:\s+aproximad[ao])?\s*(?:de|:)?\s*r?\$?\s*([0-9][0-9\.\,]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            parsed = _parse_decimal_value(match.group(1))
            if parsed is not None:
                return parsed
    return None


def _extract_fgts_missing_months_from_text(text: str) -> int | None:
    patterns = [
        r"(\d+)\s+(?:meses|compet[eê]ncias)\s+(?:sem|sem\s+dep[oó]sito|sem\s+recolhimento)\s+(?:de\s+)?fgts",
        r"fgts\s+(?:n[aã]o\s+recolhido|sem\s+recolhimento)\s+(?:por|durante)\s+(\d+)\s+(?:meses|compet[eê]ncias)",
        r"aus[eê]ncia\s+de\s+dep[oó]sitos?\s+(?:por|durante)\s+(\d+)\s+(?:meses|compet[eê]ncias)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _is_without_cause_dismissal(metadata: dict, text: str) -> bool:
    value = _metadata_first_value(
        metadata,
        [
            "dispensa_sem_justa_causa",
            "houve_dispensa_sem_justa_causa",
            "sem_justa_causa",
            "dismissal_without_cause",
            "modalidade_rescisao",
            "tipo_rescisao",
        ],
    )

    if isinstance(value, bool):
        return value

    value_text = str(value or "").lower()
    combined = f"{value_text} {text}"

    negative_markers = [
        "pedido de demissão",
        "pedido de demissao",
        "justa causa",
        "rescisão indireta",
        "rescisao indireta",
    ]
    if any(marker in combined for marker in negative_markers) and "sem justa causa" not in combined:
        return False

    return "sem justa causa" in combined or "dispensado sem justa causa" in combined


def _build_default_claim_values_section(cause_value: str) -> str:
    return "\n\n".join(
        [
            "Os pedidos deverão ser acompanhados de indicação de valores estimados ou liquidados antes do protocolo, conforme os dados disponíveis no caso e a memória de cálculo revisada pelo advogado responsável.",
            f"Valor da causa atualmente informado: R$ {cause_value}.",
            "Caso ainda não exista memória de cálculo, recomenda-se inserir os valores por pedido antes do ajuizamento, com indicação expressa de eventual natureza estimativa/preliminar.",
        ]
    )


# PATCH: editor_protocol_readiness_checklist_v1
def _has_placeholder(value: str) -> bool:
    normalized = _safe_text(value).lower()
    return (
        not normalized
        or "[" in normalized
        or "a complementar" in normalized
        or "a definir" in normalized
    )


def _build_protocol_readiness_checklist_section(
    *,
    author_inline_qualification: str,
    defendant_inline_qualification: str,
    lawyer_name: str,
    lawyer_oab: str,
    lawyer_uf: str,
    signature_local: str,
    signature_date: str,
    cause_value: str,
    is_fgts_case: bool,
) -> str:
    pending_items: list[str] = []
    ready_items: list[str] = []

    if "[CPF a complementar]" in author_inline_qualification:
        pending_items.append("Informar e conferir CPF do reclamante.")
    if "[RG a complementar]" in author_inline_qualification:
        pending_items.append("Informar e conferir RG/documento pessoal do reclamante, se necessário.")
    if "[endereço completo]" in author_inline_qualification:
        pending_items.append("Informar endereço completo do reclamante.")

    if "[CNPJ a complementar]" in defendant_inline_qualification:
        pending_items.append("Informar e conferir CNPJ da reclamada.")
    if "[endereço completo]" in defendant_inline_qualification:
        pending_items.append("Informar endereço completo da reclamada.")
    elif "sede em" in defendant_inline_qualification.lower():
        pending_items.append("Conferir se a sede/endereço da reclamada está completo para citação.")

    if _has_placeholder(lawyer_name):
        pending_items.append("Informar nome do advogado responsável.")
    if _has_placeholder(lawyer_oab) or _has_placeholder(lawyer_uf):
        pending_items.append("Informar OAB/UF do advogado responsável.")
    if _has_placeholder(signature_local):
        pending_items.append("Informar local de assinatura.")
    if _has_placeholder(signature_date):
        pending_items.append("Informar data de assinatura.")

    if _has_placeholder(cause_value):
        pending_items.append("Definir ou revisar valor da causa antes do protocolo.")
    else:
        ready_items.append(f"Valor da causa preenchido/revisável: R$ {cause_value}.")

    if is_fgts_case:
        pending_items.extend(
            [
                "Anexar extrato analítico completo do FGTS.",
                "Anexar ou conferir holerites/recibos salariais do período discutido.",
                "Anexar CTPS, contrato de trabalho ou documento equivalente.",
                "Conferir documentos rescisórios, especialmente se houver pedido de multa de 40%.",
                "Conferir GFIP, SEFIP, eSocial, fichas financeiras e comprovantes de recolhimento, quando disponíveis ou sob guarda da reclamada.",
                "Revisar memória de cálculo das competências sem recolhimento antes do ajuizamento.",
            ]
        )

    if not pending_items:
        pending_items.append("Sem pendências automatizadas identificadas; manter revisão profissional final antes do protocolo.")

    ready_items.append("Qualificação básica das partes gerada com os dados disponíveis no caso.")
    ready_items.append("Peça gerada pelo Editor Jurídico Vivo sujeita à validação do advogado responsável.")

    pending_block = "\n".join(f"- {item}" for item in dict.fromkeys(pending_items))
    ready_block = "\n".join(f"- {item}" for item in dict.fromkeys(ready_items))

    return "\n\n".join(
        [
            "Checklist interno de prontidão para protocolo. Este bloco serve como apoio operacional do escritório e deve ser revisado antes do ajuizamento.",
            f"Pendências e conferências obrigatórias:\n{pending_block}",
            f"Itens já tratados ou encaminhados pela peça:\n{ready_block}",
        ]
    )


def _build_fgts_claim_values_section(metadata: dict, case, cause_value: str) -> tuple[str, str | None]:
    combined_text = _case_combined_text(case, metadata)

    salary = _parse_decimal_value(
        _metadata_first_value(
            metadata,
            [
                "salario_mensal",
                "salario",
                "remuneracao_mensal",
                "remuneração_mensal",
                "monthly_salary",
            ],
        )
    ) or _extract_salary_from_text(combined_text)

    missing_months = _parse_int_value(
        _metadata_first_value(
            metadata,
            [
                "meses_sem_fgts",
                "competencias_sem_fgts",
                "meses_fgts_nao_recolhido",
                "fgts_missing_months",
            ],
        )
    ) or _extract_fgts_missing_months_from_text(combined_text)

    deposited = _parse_decimal_value(
        _metadata_first_value(
            metadata,
            [
                "valor_fgts_depositado",
                "fgts_depositado",
                "valor_ja_depositado_fgts",
                "fgts_already_deposited",
            ],
        )
    ) or Decimal("0")

    without_cause = _is_without_cause_dismissal(metadata, combined_text)

    missing_items = []
    if salary is None:
        missing_items.append("Informar salário/remuneração mensal base para cálculo do FGTS.")
    if missing_months is None:
        missing_items.append("Informar quantidade de meses ou competências sem recolhimento de FGTS.")
    missing_items.append("Anexar e conferir extrato analítico completo do FGTS.")
    missing_items.append("Conferir holerites, CTPS/contrato, comprovantes de pagamento, GFIP, SEFIP/eSocial e documentos rescisórios, se houver.")
    if not without_cause:
        missing_items.append("Confirmar modalidade de rescisão para definir se há multa rescisória de 40%.")

    if salary is None or missing_months is None:
        pending_lines = "\n".join(f"- {item}" for item in missing_items)
        content = "\n\n".join(
            [
                "Cálculo pendente para ajuizamento.",
                "Ainda não há base numérica mínima suficiente para liquidar ou estimar com segurança as diferenças de FGTS diretamente na peça.",
                f"Pendências de cálculo:\n{pending_lines}",
                f"Valor da causa atualmente informado: R$ {cause_value}. Caso não haja valor definitivo, o advogado deverá inserir valor estimado por pedido antes do protocolo.",
            ]
        )
        return content, None

    fgts_due = (salary * Decimal("0.08") * Decimal(missing_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    fgts_difference = max(Decimal("0"), (fgts_due - deposited).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    fgts_fine = (fgts_difference * Decimal("0.40")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if without_cause else Decimal("0")
    total = (fgts_difference + fgts_fine).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    fine_line = (
        f"II. Diferença estimada da multa rescisória de 40% sobre o FGTS, considerada a hipótese de dispensa sem justa causa: R$ {_format_brl(fgts_fine)}."
        if without_cause
        else "II. Multa rescisória de 40% sobre o FGTS: pendente de confirmação da modalidade de rescisão, não somada ao valor estimado neste momento."
    )

    content = "\n\n".join(
        [
            "Memória preliminar de cálculo para ajuizamento, sujeita à revisão do advogado responsável, conferência documental e adequação antes do protocolo.",
            f"Base informada/identificada: salário mensal de R$ {_format_brl(salary)} e {missing_months} competência(s)/mês(es) sem recolhimento integral de FGTS.",
            f"I. Diferenças estimadas de FGTS não recolhido ou recolhido a menor: R$ {_format_brl(fgts_difference)}.",
            fine_line,
            "III. Honorários advocatícios sucumbenciais: a serem estimados ou requeridos conforme estratégia profissional e percentual aplicável, sem inclusão automática nesta memória preliminar.",
            f"IV. Valor estimado da causa, limitado aos pedidos economicamente quantificados neste cálculo preliminar: R$ {_format_brl(total)}.",
            "Observação técnica: os valores possuem natureza preliminar/estimativa e devem ser confrontados com extrato analítico do FGTS, holerites, CTPS/contrato, comprovantes de pagamento, GFIP, SEFIP/eSocial, documentos rescisórios e memória de cálculo revisada antes do ajuizamento.",
        ]
    )

    return content, _format_brl(total)


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


def _series_block(title: str, items: list[str], limit: int = 4) -> str:
    normalized_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        cleaned = _safe_text(item).rstrip(".;:, ")
        if not cleaned:
            continue
        fingerprint = cleaned.lower()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized_items.append(cleaned)

    if not normalized_items:
        return ""

    lines = [title]
    for item in normalized_items[:limit]:
        lines.append(f"- {item}.")

    if len(normalized_items) > limit:
        lines.append("- Os demais pontos correlatos devem ser detalhados na versão final da minuta.")

    return "\n".join(lines)


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


def _normalize_role_token(value) -> str:
    raw = _safe_text(value).lower()
    if not raw:
        return ""
    return "".join(
        char for char in unicodedata.normalize("NFD", raw)
        if unicodedata.category(char) != "Mn"
    )


def _load_case_active_parties(db: Session, tenant_id: int, case_id: int) -> list[dict]:
    state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == tenant_id,
            CasePartyStateModel.case_id == case_id,
        )
        .order_by(CasePartyStateModel.updated_at.desc())
        .first()
    )
    if not state:
        return []

    parties = (
        db.query(CasePartyModel)
        .filter(
            CasePartyModel.tenant_id == tenant_id,
            CasePartyModel.party_state_id == state.id,
            CasePartyModel.status == "active",
        )
        .order_by(CasePartyModel.is_original_party.desc(), CasePartyModel.id.asc())
        .all()
    )

    return [
        {
            "name": party.name,
            "role": party.role,
            "party_type": party.party_type,
            "document_id": party.document_id,
            "party_metadata": party.party_metadata or {},
        }
        for party in parties
    ]


def _load_case_state_metadata(db: Session, tenant_id: int, case_id: int) -> dict:
    state = (
        db.query(CasePartyStateModel)
        .filter(
            CasePartyStateModel.tenant_id == tenant_id,
            CasePartyStateModel.case_id == case_id,
        )
        .order_by(CasePartyStateModel.updated_at.desc())
        .first()
    )
    if not state:
        return {}
    return dict(state.state_metadata or {})


def _select_primary_party(parties: list[dict], keywords: list[str]) -> dict | None:
    normalized_keywords = [_normalize_role_token(keyword) for keyword in keywords]

    for party in parties:
        role = _normalize_role_token(party.get("role"))
        role_tokens = set(role.split())

        for keyword in normalized_keywords:
            if not keyword:
                continue

            # PATCH: prevent_author_selected_as_defendant_v1
            # Termos curtos como "ré" normalizam para "re" e não podem bater
            # por substring dentro de palavras como "reclamante".
            if len(keyword) <= 2:
                if role == keyword or keyword in role_tokens:
                    return party
                continue

            if keyword in role:
                return party

    return None


def _format_party_inline_qualification(
    party: dict | None,
    fallback_name: str,
    *,
    default_is_company: bool = False,
) -> str:
    if not party:
        if default_is_company:
            return f"{fallback_name}, pessoa jurídica inscrita no CNPJ nº [CNPJ a complementar], com sede em [endereço completo]"
        return f"{fallback_name}, [nacionalidade], [estado civil], [profissão], inscrito(a) no CPF nº [CPF a complementar] e RG nº [RG a complementar], residente e domiciliado(a) em [endereço completo]"

    metadata = party.get("party_metadata") or {}
    raw_qualification = _safe_text(metadata.get("qualificacao"))
    if raw_qualification:
        return raw_qualification.rstrip(".")

    name = _safe_text(party.get("name")) or fallback_name
    document_id = (
        _safe_text(party.get("document_id"))
        or _safe_text(metadata.get("cpf"))
        or _safe_text(metadata.get("cnpj"))
    )
    address = (
        _safe_text(metadata.get("endereco"))
        or _safe_text(metadata.get("address"))
        or _safe_text(metadata.get("endereco_completo"))
        or _safe_text(metadata.get("residencia"))
        or "[endereço completo]"
    )

    normalized_party_type = _normalize_role_token(
        party.get("party_type") or metadata.get("party_type") or ""
    )
    digits = "".join(ch for ch in str(document_id) if ch.isdigit())
    is_company = default_is_company or normalized_party_type in {"company", "legal_entity", "pj", "empresa"} or len(digits) == 14

    if is_company:
        cnpj = document_id if document_id else "[CNPJ a complementar]"
        return f"{name}, pessoa jurídica inscrita no CNPJ nº {cnpj}, com sede em {address}"

    nationality = (
        _safe_text(metadata.get("nacionalidade"))
        or _safe_text(metadata.get("nationality"))
        or "[nacionalidade]"
    )
    civil_status = (
        _safe_text(metadata.get("estado_civil"))
        or _safe_text(metadata.get("estado civil"))
        or _safe_text(metadata.get("civil_status"))
        or "[estado civil]"
    )
    profession = (
        _safe_text(metadata.get("profissao"))
        or _safe_text(metadata.get("profissão"))
        or _safe_text(metadata.get("profession"))
        or _safe_text(metadata.get("occupation"))
        or "[profissão]"
    )

    cpf = document_id if document_id else "[CPF a complementar]"
    rg = _safe_text(metadata.get("rg")) or "[RG a complementar]"
    return f"{name}, {nationality}, {civil_status}, {profession}, inscrito(a) no CPF nº {cpf} e RG nº {rg}, residente e domiciliado(a) em {address}"


# PATCH: editor_extract_parties_from_description_v1
def _extract_labor_parties_from_case_description(case_description: str) -> list[dict]:
    """
    Extrai partes mínimas da descrição quando ainda não há CasePartyState estruturado.

    Não inventa CPF, CNPJ ou endereço completo. Apenas aproveita dados explícitos
    do texto do caso para reduzir placeholders na peça.
    """
    text = _safe_text(case_description)
    if not text:
        return []

    parties: list[dict] = []

    author_match = re.search(
        r"parte\s+reclamante\s*:\s*(?P<name>[^\n,\.]+)",
        text,
        flags=re.IGNORECASE,
    )
    profession_match = re.search(
        r"exercendo\s+a\s+fun[cç][aã]o\s+de\s+(?P<profession>[^,\n\.]+)",
        text,
        flags=re.IGNORECASE,
    )

    if author_match:
        author_name = author_match.group("name").strip(" .")
        profession = (
            profession_match.group("profession").strip(" .")
            if profession_match
            else ""
        )
        parties.append(
            {
                "name": author_name,
                "role": "reclamante",
                "party_type": "person",
                "document_id": "",
                "party_metadata": {
                    "profissao": profession or "[profissão]",
                    "qualificacao_source": "case_description_fallback",
                },
            }
        )

    defendant_match = re.search(
        r"parte\s+reclamada\s*:\s*(?P<raw>[^\n]+)",
        text,
        flags=re.IGNORECASE,
    )

    if defendant_match:
        raw_defendant = defendant_match.group("raw").strip(" .")
        defendant_name = raw_defendant
        address = "[endereço completo]"

        if "," in raw_defendant:
            first, rest = raw_defendant.split(",", 1)
            defendant_name = first.strip(" .")
            address_candidate = rest.strip(" .")
            if address_candidate:
                address = address_candidate

        parties.append(
            {
                "name": defendant_name,
                "role": "reclamada",
                "party_type": "company",
                "document_id": "",
                "party_metadata": {
                    "endereco": address,
                    "qualificacao_source": "case_description_fallback",
                },
            }
        )

    return parties


def _build_assisted_sections(
    db: Session,
    case: Case,
    analysis_record,
    tenant_id: int,
    document_metadata: dict | None = None,
) -> list[dict]:
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
    if executive_summary:
        import re as _re

        executive_summary = _re.sub(
            r",?\s*com probabilidade estimada de êxito em\s+\d+%\.?",
            ".",
            executive_summary,
            flags=_re.IGNORECASE,
        )
        executive_summary = _re.sub(
            r"probabilidade estimada\s*:?\s*\d+%\.?",
            "avaliação qualitativa, sem previsão percentual de resultado judicial.",
            executive_summary,
            flags=_re.IGNORECASE,
        )
        executive_summary = executive_summary.replace("..", ".").strip()

    final_status = _safe_text(decision.get("final_status") if isinstance(decision, dict) else "")
    normalized_area = str(getattr(case, "legal_area", "") or "").strip().lower()
    normalized_action_type = str(getattr(case, "action_type", "") or "").strip().lower()
    case_search_text = " ".join(
        [
            str(getattr(case, "title", "") or ""),
            str(getattr(case, "description", "") or ""),
            normalized_action_type,
        ]
    ).lower()
    is_civel_area = normalized_area in {"civel", "civil_ambiental"}
    is_trabalhista_area = normalized_area in {"trabalhista", "trabalho", "laboral"}
    is_civel_cobranca = is_civel_area and any(
        marker in case_search_text
        for marker in ["cobran", "inadimpl", "dívida", "divida", "saldo contratual", "contrato de prestação"]
    )
    is_trabalhista_insalubridade_periculosidade = is_trabalhista_area and any(
        marker in case_search_text
        for marker in [
            "insalubr",
            "periculos",
            "calor",
            "fusão",
            "fusao",
            "metal em fusão",
            "metal em fusao",
            "epi",
            "ppp",
            "ltcat",
            "pgr",
            "pcmso",
        ]
    )
    controverted_points = list(dict.fromkeys([item for item in [*issues, *critical_points] if item]))
    proof_checklist = list(dict.fromkeys([item for item in [*probative_gaps, *next_steps] if item]))

    if is_civel_cobranca:
        cleaned_proof_checklist = []
        for item in proof_checklist:
            item_text = str(item or "").strip()
            item_lower = item_text.lower()

            if "persistência da conduta" in item_lower:
                cleaned_proof_checklist.append(
                    "Necessidade de cronologia objetiva dos vencimentos, pagamentos realizados, mora, tentativas de cobrança e saldo atualizado."
                )
                continue

            if any(
                forbidden in item_lower
                for forbidden in [
                    "ambiental",
                    "acústica",
                    "acustica",
                    "mitigação",
                    "mitigacao",
                    "obrigação de fazer",
                    "obrigacao de fazer",
                    "não fazer",
                    "nao fazer",
                    "impactos narrados",
                    "reiteração dos impactos",
                ]
            ):
                continue

            cleaned_proof_checklist.append(item_text)

        proof_checklist = list(dict.fromkeys([item for item in cleaned_proof_checklist if item]))


    is_trabalhista_verbas_rescisorias = is_trabalhista_area and (
        any(
            term in case_search_text
            for term in [
                "verbas rescisórias",
                "verbas rescisorias",
                "dispensa sem justa causa",
                "saldo de salário",
                "saldo de salario",
                "aviso-prévio",
                "aviso previo",
                "aviso prévio",
                "13º salário",
                "13o salario",
                "art. 477",
                "art. 467",
            ]
        )
        or (
            ("rescisão" in case_search_text or "rescisao" in case_search_text)
            and any(
                term in case_search_text
                for term in [
                    "saldo de salário",
                    "saldo de salario",
                    "aviso-prévio",
                    "aviso previo",
                    "férias proporcionais",
                    "ferias proporcionais",
                    "13º salário",
                    "13o salario",
                ]
            )
        )
    )

    is_trabalhista_horas_extras = is_trabalhista_area and any(
        term in case_search_text
        for term in [
            "horas extras",
            "hora extra",
            "jornada excedente",
            "jornada superior",
            "jornada habitual",
            "intervalo intrajornada",
            "intervalo reduzido",
            "intervalo irregular",
            "controle de ponto",
            "controles de ponto",
            "cartão de ponto",
            "cartao de ponto",
            "cartões de ponto",
            "cartoes de ponto",
            "dsr",
            "descanso semanal remunerado",
            "adicional de horas extras",
            "escala de trabalho",
            "escalas de trabalho",
        ]
    )


    is_trabalhista_fgts_nao_recolhido = is_trabalhista_area and any(
        term in case_search_text
        for term in [
            "fgts não recolhido",
            "fgts nao recolhido",
            "depósitos de fgts",
            "depositos de fgts",
            "depósitos mensais de fgts",
            "depositos mensais de fgts",
            "depósitos parciais",
            "depositos parciais",
            "depósitos irregulares",
            "depositos irregulares",
            "ausência de depósitos",
            "ausencia de depositos",
            "extrato analítico do fgts",
            "extrato analitico do fgts",
            "extrato do fgts",
            "conta vinculada",
            "saldo fundiário",
            "saldo fundiario",
            "regularização de depósitos",
            "regularizacao de depositos",
            "diferenças de fgts",
            "diferencas de fgts",
            "gfip",
            "sefip",
            "esocial",
            "recolhimento de fgts",
        ]
    )

    if is_trabalhista_insalubridade_periculosidade:
        labor_proof_checklist = []
        for item in proof_checklist:
            item_text = str(item or "").strip()
            item_lower = item_text.lower()

            if "laudo/relatório médico" in item_lower or "relatório médico" in item_lower:
                labor_proof_checklist.append(
                    "Necessidade de prova técnica ambiental/pericial para aferir exposição a calor, proximidade com metal em fusão, condições do setor de fusão e eventual neutralização por EPI."
                )
                continue

            if "persistência da conduta" in item_lower:
                labor_proof_checklist.append(
                    "Necessidade de confirmação da rotina real de trabalho, frequência da exposição, distância da fonte de calor, EPIs fornecidos e eficácia da proteção."
                )
                continue

            labor_proof_checklist.append(item_text)

        labor_proof_checklist.extend(
            [
                "Necessidade de obtenção e análise de PPP, LTCAT, PGR, PCMSO, mapa de riscos e ficha de entrega de EPI.",
                "Necessidade de cálculo trabalhista preliminar considerando adicional de insalubridade em grau eventualmente apurado, ou periculosidade de forma subsidiária, com reflexos em férias + 1/3, 13º salário, FGTS e demais verbas cabíveis.",
            ]
        )
        proof_checklist = list(dict.fromkeys([item for item in labor_proof_checklist if item]))

    active_parties = _load_case_active_parties(db, tenant_id, case.id)
    state_metadata = _load_case_state_metadata(db, tenant_id, case.id)
    # PATCH: pass_document_metadata_to_assisted_sections_v1
    # Dados do documento aprovado/atual entram como complemento para cálculo e fechamento da peça.
    if isinstance(document_metadata, dict) and document_metadata:
        state_metadata = {
            **state_metadata,
            **document_metadata,
        }

    case_comarca = _safe_text(state_metadata.get("case_comarca")) or "[COMARCA A DEFINIR PELO ADVOGADO]"
    cause_value = _safe_text(state_metadata.get("cause_value")) or "[valor a ser definido pelo advogado]"
    pedidos_valores_estimados = _build_default_claim_values_section(cause_value)
    lawyer_name = _safe_text(state_metadata.get("lawyer_name")) or "[Nome do advogado]"
    lawyer_oab = _safe_text(state_metadata.get("lawyer_oab")) or "[número]"
    lawyer_uf = _safe_text(state_metadata.get("lawyer_uf")) or "[UF]"
    signature_local = _safe_text(state_metadata.get("signature_local")) or "[Local]"
    signature_date = _safe_text(state_metadata.get("signature_date")) or "[data]"

    normalized_area_text = f"{normalized_area}".lower()
    is_labor_case = (
        is_trabalhista_area
        or is_trabalhista_insalubridade_periculosidade
        or "trabalh" in normalized_area_text
        or "reclamação trabalhista" in case_search_text
        or "reclamacao trabalhista" in case_search_text
        or "vara do trabalho" in case_search_text
        or "adicional de insalubridade" in case_search_text
        or "adicional de periculosidade" in case_search_text
        or "verbas rescisórias" in case_search_text
        or "verbas rescisorias" in case_search_text
        or "dispensa sem justa causa" in case_search_text
        or "multa de 40" in case_search_text
        or "trct" in case_search_text
        or "horas extras" in case_search_text
        or "jornada excedente" in case_search_text
        or "intervalo intrajornada" in case_search_text
        or "controle de ponto" in case_search_text
        or "fgts não recolhido" in case_search_text
        or "fgts nao recolhido" in case_search_text
        or "extrato analítico do fgts" in case_search_text
        or "extrato analitico do fgts" in case_search_text
        or "depósitos de fgts" in case_search_text
        or "depositos de fgts" in case_search_text
        or "conta vinculada" in case_search_text
        or ("reclamante" in case_search_text and "reclamada" in case_search_text)
    )

    active_parties = _load_case_active_parties(db, tenant_id, case.id)
    if not active_parties:
        active_parties = _extract_labor_parties_from_case_description(case_description)

    author_party = _select_primary_party(
        active_parties,
        ["autor", "autora", "parte autora", "requerente", "demandante", "reclamante", "impetrante"],
    )
    defendant_party = _select_primary_party(
        active_parties,
        ["reu", "ré", "réu", "parte re", "parte ré", "requerido", "demandado", "reclamada", "impetrado"],
    )

    if author_party is None and active_parties:
        author_party = active_parties[0]

    if defendant_party is None or defendant_party is author_party:
        defendant_party = next((party for party in active_parties if party is not author_party), None)

    author_inline_qualification = _format_party_inline_qualification(
        author_party,
        "[NOME COMPLETO DA PARTE AUTORA]",
    )
    defendant_inline_qualification = _format_party_inline_qualification(
        defendant_party,
        "[NOME/RAZÃO SOCIAL DA PARTE RÉ]",
        default_is_company=True,
    )

    missing_items = _build_missing_context_items(
        case_description=case_description,
        technical_summary=technical_summary,
        issues=issues,
        next_steps=next_steps,
    )

    insufficient_context = (
        len(case_description) < 80
        or not technical_summary
        or "apenas identificador" in f"{case_description} {technical_summary}".lower()
        or "dados insuficientes" in f"{case_description} {technical_summary}".lower()
        or (len(case_description) < 140 and len(proof_checklist) >= 2)
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
                "missing_items": missing_items,
                "guidance_title": "O que falta preencher antes de concluir este bloco",
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
                "missing_items": missing_items,
                "guidance_title": "O que falta preencher antes de concluir este bloco",
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
                "missing_items": missing_items,
                "guidance_title": "O que falta preencher antes de concluir este bloco",
                },
            },
        ]

    resumo_fatico = _paragraphs(
        [
            f"Trata-se do caso {case.case_number} — {case.title}.",
            case_description,
            (
                "A narrativa fática acima deverá ser revisada e completada, na versão final, com datas, períodos, documentos e demais elementos concretos já disponíveis no caso."
                if len(case_description) < 220
                else ""
            ),
        ]
    )

    fundamentacao = _paragraphs(
        [
            (
                "I. Do cabimento da pretensão. À luz do quadro fático descrito, a demanda deve ser estruturada como ação de cobrança contratual, voltada à condenação da parte ré ao pagamento do saldo inadimplido, com os encargos contratuais e legais cabíveis."
                if is_civel_cobranca
                else (
                    "I. Do cabimento da pretensão. À luz do quadro fático descrito, a demanda deve ser estruturada para cessar a lesão narrada, recompor o status jurídico violado e prevenir a reiteração dos impactos ao direito material discutido."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "I. Do cabimento da pretensão. À luz do quadro fático narrado, a demanda deve ser estruturada para tutelar o direito material afirmado e enfrentar a controvérsia central com base na prova já disponível."
                )
            ),
            (
                "II. Dos fundamentos jurídicos da cobrança. A pretensão deve se apoiar na existência de relação contratual, no cumprimento da prestação pela parte autora, no inadimplemento das parcelas vencidas pela parte ré, na mora e na responsabilidade pelo pagamento do principal, multa, juros, correção monetária, custas e honorários."
                if is_civel_cobranca
                else _series_block("II. Dos fundamentos normativos aplicáveis:", normative_basis, limit=5)
            ),
            (
                f"III. Da estratégia jurídica sugerida. {recommended_strategy}"
                if recommended_strategy
                else "III. Da estratégia jurídica sugerida. A condução da tese deve priorizar coerência entre narrativa fática, prova disponível, pedido principal e tutela pretendida."
            ),
            _series_block("IV. Dos pontos controvertidos que exigem enfrentamento direto:", controverted_points, limit=5),
            _series_block("V. Das lacunas probatórias a suprir antes do protocolo definitivo:", proof_checklist, limit=5),
            (
                f"VI. Da síntese conclusiva considerada na redação. {executive_summary}"
                if executive_summary and "dados insuficientes" not in executive_summary.lower()
                else ""
            ),
        ]
    )

    pedidos = _paragraphs(
        [
            (
                "I. Requer-se a citação da parte ré para, querendo, apresentar contestação, sob pena de revelia e confissão quanto à matéria de fato."
                if is_civel_cobranca
                else (
                    "I. Requer-se, em tutela provisória de urgência, quando presentes os requisitos legais, a imediata cessação, redução ou mitigação dos impactos narrados, inclusive por obrigação de fazer e/ou não fazer."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "I. Requer-se, quando presentes os requisitos legais, a concessão da tutela provisória cabível para resguardar desde logo a utilidade do provimento final."
                )
            ),
            (
                "II. Requer-se a condenação da parte ré ao pagamento do saldo contratual inadimplido, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios."
                if is_civel_cobranca
                else _series_block("II. Pedidos principais sugeridos para a minuta final:", issues, limit=5)
            ),
            (
                "III. Requer-se que os encargos de mora sejam calculados a partir do vencimento de cada parcela inadimplida, observando-se a cláusula contratual aplicável e a planilha de cálculo a ser juntada na versão final."
                if is_civel_cobranca
                else (
                    "III. Requer-se, ao final, a procedência dos pedidos principais, com imposição das obrigações materiais compatíveis com a narrativa, a prova produzida e a extensão do dano demonstrado."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "III. Requer-se, ao final, a procedência dos pedidos compatíveis com os fatos narrados, a tese sustentada e a prova disponível."
                )
            ),
            (
                "IV. Requer-se a produção de prova documental suplementar, testemunhal e demais meios de prova em direito admitidos, especialmente contrato, comprovantes de pagamento, relatório técnico, fotografias, mensagens, notificação extrajudicial, e-mails e planilha de cálculo."
                if is_civel_cobranca
                else "IV. Requer-se, ainda, a citação da parte ré, a produção de prova documental, testemunhal e pericial, bem como os requerimentos acessórios pertinentes ao rito e à estratégia processual adotada."
            ),
            (
                "V. Requer-se a condenação da parte ré ao pagamento das custas processuais e honorários advocatícios, nos termos da legislação processual aplicável."
                if is_civel_cobranca
                else (
                    f"V. O enquadramento provisório da análise indica a seguinte diretriz para fechamento dos pedidos: {final_status}."
                    if final_status and "dados insuficientes" not in final_status.lower()
                    else ""
                )
            ),
            (
                "VI. Antes do protocolo definitivo, o advogado deverá revisar valor da causa, memória de cálculo, índice de correção monetária, competência territorial e documentos comprobatórios do inadimplemento."
                if is_civel_cobranca
                else "VI. Antes do protocolo definitivo, o advogado deverá revisar a aderência entre pedidos, causa de pedir, prova disponível, tutela de urgência e liquidez dos danos postulados."
            ),
        ]
    )

    enderecamento = _paragraphs(
        [
            (
                f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DE UMA DAS VARAS CÍVEIS DA COMARCA DE {case_comarca}."
                if normalized_area in {"civel", "civil_ambiental"}
                else f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DO JUÍZO COMPETENTE DA COMARCA DE {case_comarca}."
            ),
            "Na versão final, o advogado deverá confirmar a competência territorial, o órgão jurisdicional, eventual prevenção e o rito adequado antes do protocolo.",
        ]
    )

    qualificacao_partes = _paragraphs(
        [
            f"{author_inline_qualification}, por seu advogado, vem, respeitosamente, à presença de Vossa Excelência, propor a presente demanda em face de {defendant_inline_qualification}.",
            "Na revisão final, deverão ser confirmados os dados completos de qualificação, a legitimidade ativa e passiva, a existência de representantes, sucessores, litisconsortes e demais elementos subjetivos relevantes ao caso.",
            "Se houver representantes, espólio, sucessores, litisconsórcio ou pessoa jurídica no polo passivo, complementar a qualificação com os dados formais constantes dos documentos do caso.",
        ]
    )

    provas_requerimentos = _paragraphs(
        [
            "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente documental, testemunhal e pericial, conforme a natureza das controvérsias identificadas.",
            (
                "Na versão final, devem ser especificados e anexados os documentos de cobrança: contrato assinado, comprovante de pagamento parcial, relatório de execução dos serviços, fotografias, mensagens de reconhecimento da dívida, notificação extrajudicial, e-mails e planilha de cálculo atualizada."
                if is_civel_cobranca
                else (
                    "Na versão final, devem ser especificados os documentos já existentes, a necessidade de prova técnica ambiental/acústica, eventual inspeção judicial e o fundamento da tutela de urgência."
                    if normalized_area in {"civel", "civil_ambiental"}
                    else "Na versão final, devem ser especificados os documentos já existentes, a prova técnica pertinente e os requerimentos probatórios adequados ao caso."
                )
            ),
            (
                "Também devem ser ajustados os requerimentos acessórios, especialmente valor da causa, memória de cálculo, índice de correção monetária, comprovação de mora e eventual tentativa extrajudicial de composição."
                if is_civel_cobranca
                else "Também devem ser ajustados os requerimentos acessórios, a intimação da parte contrária e as providências processuais cabíveis ao rito escolhido."
            ),
        ]
    )

    fechamento = _paragraphs(
        [
            "Ante o exposto, requer o regular processamento da presente demanda e, ao final, o acolhimento dos pedidos formulados, nos limites da narrativa fática, da prova produzida e da estratégia jurídica consolidada na versão final da peça.",
            "Protesta por todos os meios de prova em direito admitidos, especialmente documental, testemunhal e pericial, sem prejuízo de outros que se tornem necessários no curso da instrução.",
            f"Dá-se à causa o valor de R$ {cause_value}, sujeito a ajuste conforme os critérios legais aplicáveis e a consolidação definitiva dos pedidos.",
            "Termos em que, pede deferimento.",
            f"{signature_local}, {signature_date}.",
            f"{lawyer_name} — OAB/{lawyer_uf} {lawyer_oab}.",
        ]
    )

    if is_civel_cobranca:
        import re

        civil_case_comarca = case_comarca
        if civil_case_comarca.startswith("[") and ("itapoá" in case_search_text or "itapoa" in case_search_text):
            civil_case_comarca = "ITAPOÁ/SC"

        def _parse_brl_amount(value: str) -> float:
            return float(value.replace(".", "").replace(",", "."))

        def _format_brl_amount(value: float) -> str:
            formatted = f"{value:,.2f}"
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

        civil_cause_value = cause_value
        if civil_cause_value.startswith("["):
            cause_match = re.search(
                r"(?:saldo principal|d[ií]vida principal|valor principal)(?:[^R]{0,120})R\$\s*([\d\.\,]+)",
                case_description,
                flags=re.IGNORECASE,
            )
            if not cause_match:
                cause_match = re.search(
                    r"principal de R\$\s*([\d\.\,]+)",
                    case_description,
                    flags=re.IGNORECASE,
                )
            if cause_match:
                civil_cause_value = cause_match.group(1).strip().rstrip(".;:")
            else:
                open_marker_match = re.search(
                    r"(?:permaneceram em aberto|parcelas? em aberto|saldo em aberto)",
                    case_description,
                    flags=re.IGNORECASE,
                )
                if open_marker_match:
                    open_window = case_description[
                        open_marker_match.start() : open_marker_match.start() + 450
                    ]
                    installment_values = re.findall(
                        r"R\$\s*([\d]{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})",
                        open_window,
                        flags=re.IGNORECASE,
                    )
                    if installment_values:
                        total = sum(_parse_brl_amount(item) for item in installment_values)
                        civil_cause_value = _format_brl_amount(total)

        company_match = re.search(
            r"A empresa\s+(.+?)\s+foi contratada pela empresa\s+(.+?)\s+para",
            case_description,
            flags=re.IGNORECASE | re.DOTALL,
        )
        structured_author_match = re.search(
            r"^\s*Autor(?:a)?\s*:\s*(.+?)\s*$",
            case_description,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        structured_defendant_match = re.search(
            r"^\s*R[ée]u\s*:\s*(.+?)\s*$",
            case_description,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        civil_author_name = ""
        civil_defendant_name = ""

        if company_match:
            civil_author_name = _safe_text(company_match.group(1))
            civil_defendant_name = _safe_text(company_match.group(2))
        elif structured_author_match or structured_defendant_match:
            civil_author_name = _safe_text(structured_author_match.group(1)) if structured_author_match else ""
            civil_defendant_name = _safe_text(structured_defendant_match.group(1)) if structured_defendant_match else ""

        civil_author_name = civil_author_name.strip().rstrip(".;:")
        civil_defendant_name = civil_defendant_name.strip().rstrip(".;:")

        if civil_author_name:
            author_inline_qualification = (
                f"{civil_author_name.upper()}, pessoa jurídica de direito privado, "
                "inscrita no CNPJ sob nº [CNPJ a complementar], com sede em [endereço completo a complementar], "
                "neste ato representada na forma de seu contrato social"
            )
        if civil_defendant_name:
            defendant_inline_qualification = (
                f"{civil_defendant_name.upper()}, pessoa jurídica de direito privado, "
                "inscrita no CNPJ sob nº [CNPJ a complementar], com sede em [endereço completo a complementar]"
            )

        civil_summary = case_description.strip()
        for marker in ("Documentos disponíveis:", "Pedido pretendido:", "Observação estratégica:"):
            idx = civil_summary.lower().find(marker.lower())
            if idx >= 0:
                civil_summary = civil_summary[:idx].strip()
                break

        resumo_fatico = _paragraphs(
            [
                civil_summary,
                "Diante do inadimplemento contratual e da ausência de solução extrajudicial, a presente ação busca a condenação da parte ré ao pagamento do saldo contratual devido, acrescido dos encargos contratuais e legais cabíveis, além de custas processuais e honorários advocatícios.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. DA RELAÇÃO CONTRATUAL E DO CUMPRIMENTO DA OBRIGAÇÃO PELA AUTORA",
                "Conforme demonstram os documentos que instruem a presente demanda, a parte autora foi contratada pela parte ré para a execução dos serviços contratados descritos na narrativa fática e comprovados pelos documentos do caso.",
                "A autora cumpriu integralmente a obrigação assumida, executando os serviços contratados, com emissão de relatório técnico de conclusão, fotografias do serviço realizado e demais documentos comprobatórios da efetiva prestação dos serviços.",
                "Além disso, a própria ré efetuou o pagamento da primeira parcela contratual, o que reforça a existência da relação jurídica, a validade do ajuste firmado entre as partes e o início regular da execução contratual.",
                "II. DO INADIMPLEMENTO CONTRATUAL DA RÉ",
                "Embora a autora tenha cumprido sua obrigação contratual, a ré deixou de pagar as parcelas finais ajustadas, totalizando saldo principal inadimplido indicado na documentação do caso.",
                "A inadimplência permaneceu mesmo após tentativas extrajudiciais de solução. A ré reconheceu a existência da dívida por mensagens de WhatsApp e, posteriormente, mesmo notificada, não realizou a quitação do débito nem apresentou proposta formal de acordo.",
                "III. DA MORA E DOS ENCARGOS CONTRATUAIS E LEGAIS",
                "O inadimplemento das parcelas vencidas colocou a ré em mora, tornando exigível o pagamento do saldo contratual em aberto, acrescido dos encargos previstos no contrato e dos consectários legais cabíveis.",
                f"O débito principal corresponde a R$ {civil_cause_value}, sem prejuízo da incidência de multa contratual, juros de mora e correção monetária, conforme previsão contratual e memória de cálculo a ser atualizada até a data do ajuizamento.",
                "Assim, a ré deve responder pelo pagamento do valor principal, acrescido de multa, juros, atualização monetária, custas processuais e honorários advocatícios, em razão do descumprimento da obrigação assumida.",
                "IV. DA PROVA DOCUMENTAL DO DÉBITO",
                "A pretensão da autora está amparada por conjunto probatório documental robusto, composto por contrato de prestação de serviços assinado pelas partes, comprovante de pagamento parcial, relatório técnico de execução, fotografias do serviço concluído, conversas de WhatsApp com reconhecimento da dívida, notificação extrajudicial, e-mails trocados entre as empresas e planilha de cálculo.",
                "Tais documentos demonstram a existência da contratação, a efetiva execução dos serviços, o pagamento parcial, o inadimplemento das parcelas finais e a tentativa extrajudicial de recebimento do crédito.",
                "Eventual alegação defensiva de vício no serviço, compensação ou discordância quanto à execução deverá ser comprovada pela ré, pois a documentação disponível indica que os serviços foram concluídos e que a dívida foi posteriormente reconhecida.",
                "V. DO CABIMENTO DA AÇÃO DE COBRANÇA",
                "Diante da existência de relação contratual, da execução dos serviços pela autora e do inadimplemento da ré, é cabível a presente ação de cobrança, com o objetivo de obter a condenação da parte ré ao pagamento do saldo contratual inadimplido.",
                f"A demanda busca o recebimento do valor principal de R$ {civil_cause_value}, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios, nos termos do contrato, da legislação civil aplicável e da prova documental juntada aos autos.",
            ]
        )

        pedidos = _paragraphs(
            [
                "I. Requer-se a citação da parte ré para, querendo, apresentar contestação, sob pena de revelia e confissão quanto à matéria de fato.",
                f"II. Requer-se a condenação da parte ré ao pagamento do saldo contratual inadimplido no valor principal de R$ {civil_cause_value}, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios.",
                "III. Requer-se que os encargos de mora sejam calculados a partir do vencimento de cada parcela inadimplida, observando-se a cláusula contratual aplicável e a planilha de cálculo a ser juntada aos autos.",
                "IV. Requer-se a produção de prova documental suplementar, testemunhal e demais meios de prova em direito admitidos, especialmente contrato, comprovantes de pagamento, relatório técnico, fotografias, mensagens, notificação extrajudicial, e-mails e planilha de cálculo.",
                "V. Requer-se a condenação da parte ré ao pagamento das custas processuais e honorários advocatícios, nos termos da legislação processual aplicável.",
            ]
        )

        civil_has_defined_comarca = not civil_case_comarca.startswith("[")
        civil_enderecamento_text = (
            f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA VARA CÍVEL DA COMARCA DE {civil_case_comarca}."
            if civil_has_defined_comarca
            else "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA VARA CÍVEL DA COMARCA COMPETENTE."
        )
        civil_signature_local = (
            civil_case_comarca.replace("/Sc", "/SC").replace("/sc", "/SC").title().replace("/Sc", "/SC")
            if civil_has_defined_comarca
            else "[local a definir]"
        )

        enderecamento = _paragraphs(
            [
                civil_enderecamento_text,
            ]
        )

        qualificacao_partes = _paragraphs(
            [
                f"{author_inline_qualification}, por seu advogado infra-assinado, vem, respeitosamente, à presença de Vossa Excelência, propor a presente AÇÃO DE COBRANÇA em face de {defendant_inline_qualification}, pelos fatos e fundamentos a seguir expostos.",
            ]
        )

        pedidos_valores_estimados = _paragraphs(
            [
                f"O valor principal inadimplido corresponde a R$ {civil_cause_value}, referente ao saldo contratual em aberto indicado nos documentos do caso.",
                "Sobre o valor principal deverão incidir multa contratual, juros de mora e correção monetária, conforme previsão contratual e memória de cálculo a ser revisada e atualizada até a data do ajuizamento.",
                f"Dá-se à causa, para fins fiscais e processuais, o valor inicial de R$ {civil_cause_value}, correspondente ao saldo principal inadimplido, sem prejuízo da atualização por multa contratual, juros de mora e correção monetária conforme memória de cálculo a ser apresentada.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente prova documental suplementar e testemunhal.",
                "Deverão instruir a demanda, conforme disponibilidade e conferência do advogado responsável, o contrato assinado, comprovante de pagamento parcial, relatório de execução dos serviços, fotografias, mensagens de reconhecimento da dívida, notificação extrajudicial, e-mails e planilha de cálculo atualizada.",
            ]
        )

        fechamento = _paragraphs(
            [
                f"Ante o exposto, requer o regular processamento da presente demanda e, ao final, a total procedência dos pedidos, com a condenação da parte ré ao pagamento do saldo contratual inadimplido no valor principal de R$ {civil_cause_value}, acrescido de multa contratual, juros de mora, correção monetária, custas processuais e honorários advocatícios.",
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente prova documental suplementar, testemunhal e demais provas necessárias à demonstração da relação contratual, da execução dos serviços, do pagamento parcial, do inadimplemento e das tentativas extrajudiciais de cobrança.",
                f"Dá-se à causa, para fins fiscais e processuais, o valor inicial de R$ {civil_cause_value}, correspondente ao saldo principal inadimplido, sem prejuízo da atualização por multa contratual, juros de mora e correção monetária conforme memória de cálculo a ser apresentada.",
                "Termos em que, pede deferimento.",
                f"{civil_signature_local}, {signature_date}.",
                f"{lawyer_name} — OAB/{lawyer_uf} {lawyer_oab}.",
            ]
        )

    if is_labor_case:
        labor_jurisdiction = "JOINVILLE/SC" if "joinville" in case_search_text else "[LOCALIDADE A DEFINIR]"
        enderecamento = _paragraphs(
            [
                f"EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DA ___ VARA DO TRABALHO DE {labor_jurisdiction}.",
                "Na versão final, o advogado deverá confirmar a competência territorial, a Vara do Trabalho competente, o rito aplicável e eventual necessidade de adequação do endereçamento antes do protocolo.",
            ]
        )

    if is_trabalhista_insalubridade_periculosidade:
        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da pretensão trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à apuração de adicional de insalubridade por exposição a calor intenso e, de forma subsidiária, adicional de periculosidade caso a prova técnica demonstre risco acentuado juridicamente enquadrável.",
                "II. Dos fundamentos normativos aplicáveis. A pretensão deve observar a CLT, a Constituição Federal, as Normas Regulamentadoras de saúde e segurança do trabalho, especialmente os parâmetros técnicos relacionados à insalubridade, periculosidade, fornecimento de EPI, prova pericial e documentação ambiental/ocupacional.",
                "III. Da estratégia jurídica sugerida. A condução da tese deve priorizar prova técnica, documentação ocupacional e cálculo trabalhista preliminar, sem promessa de resultado judicial e com validação profissional antes do protocolo.",
                _series_block("IV. Dos pontos controvertidos que exigem enfrentamento direto:", controverted_points, limit=6),
                _series_block("V. Das lacunas probatórias a suprir antes do protocolo definitivo:", proof_checklist, limit=6),
                (
                    f"VI. Da síntese conclusiva considerada na redação. {executive_summary}"
                    if executive_summary and "dados insuficientes" not in executive_summary.lower()
                    else ""
                ),
            ]
        )

        pedidos = _paragraphs(
            [
                "I. Requer-se o reconhecimento do direito ao adicional de insalubridade, em grau a ser apurado por prova técnica, em razão da exposição habitual a calor intenso no setor de fusão.",
                "II. Subsidiariamente, caso a prova técnica indique enquadramento em situação de risco acentuado, requer-se a análise do adicional de periculosidade, observada a impossibilidade de cumulação entre insalubridade e periculosidade.",
                "III. Requer-se a condenação da reclamada ao pagamento das diferenças de adicional eventualmente reconhecidas no período contratual indicado na narrativa fática.",
                "IV. Requer-se a condenação da reclamada ao pagamento dos reflexos do adicional reconhecido em férias acrescidas de 1/3, 13º salário, FGTS e demais verbas trabalhistas cabíveis, conforme cálculo a ser apresentado e revisado pelo advogado.",
                "V. Requer-se a produção de prova pericial técnica no ambiente de trabalho, ou por meio técnico equivalente, a fim de verificar exposição a calor, condições do setor de fusão, fornecimento e eficácia dos EPIs.",
                "VI. Requer-se que a reclamada apresente PPP, LTCAT, PGR, PCMSO, mapa de riscos, ficha de entrega de EPI, registros de treinamento, holerites e demais documentos ambientais e ocupacionais relacionados ao período contratual.",
                "VII. Requer-se a produção de prova documental, testemunhal e pericial, sem prejuízo de outros meios de prova admitidos em direito.",
                "VIII. Requer-se, ao final, a procedência dos pedidos, nos limites da prova produzida, com juros, correção monetária, custas e demais cominações legais aplicáveis.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer-se a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e pericial técnica.",
                "Requer-se a realização de perícia técnica para aferir a exposição a calor, proximidade com metal em fusão, condições ambientais do setor de fusão, fornecimento, adequação e eficácia dos EPIs.",
                "Requer-se que a reclamada seja intimada a apresentar PPP, LTCAT, PGR, PCMSO, mapa de riscos, ficha de entrega de EPI, registros de treinamento, holerites, documentos ambientais e demais registros ocupacionais do período contratual.",
                "Na versão final, o advogado deverá ajustar valor da causa, memória de cálculo, reflexos trabalhistas, grau de insalubridade eventualmente postulado e eventual pedido subsidiário de periculosidade conforme a prova disponível.",
            ]
        )



    # PATCH: labor_insalubridade_final_text_v1
    if is_trabalhista_insalubridade_periculosidade:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à apuração de eventual direito ao adicional de insalubridade por exposição ocupacional ao calor e, de forma subsidiária, ao adicional de periculosidade, conforme as condições reais de trabalho a serem demonstradas nos autos.",
                "O reclamante afirma ter laborado em ambiente industrial ligado ao setor de fusão, com possível exposição habitual a calor intenso, proximidade de fontes térmicas relevantes e processo produtivo envolvendo metal em fusão em temperatura aproximada de 1.500°C. Ressalta-se que essa referência diz respeito à temperatura do processo industrial, não significando, por si só, a temperatura efetivamente suportada pelo trabalhador, circunstância que deverá ser apurada por prova técnica.",
                "Segundo a narrativa apresentada, durante o contrato de trabalho não teria havido pagamento de adicional de insalubridade ou periculosidade relacionado às condições ambientais do setor de fusão, embora o reclamante alegue ter exercido suas atividades em ambiente potencialmente agressivo à saúde e/ou à integridade física.",
                "A controvérsia principal consiste em verificar se as condições reais de trabalho caracterizavam exposição ocupacional a calor acima dos limites juridicamente toleráveis, apta a ensejar o pagamento de adicional de insalubridade. De forma subsidiária, deverá ser analisada eventual periculosidade, caso a prova técnica identifique situação de risco acentuado juridicamente enquadrável.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de documentos trabalhistas e ocupacionais, tais como holerites, contrato de trabalho, PPP, LTCAT, PGR, PCMSO, mapa de riscos, fichas de entrega de EPI, registros de treinamento, bem como a produção de prova testemunhal e pericial, a fim de verificar a rotina efetiva de trabalho, a frequência da exposição, a proximidade das fontes de calor, as pausas existentes, o fornecimento e a eficácia dos equipamentos de proteção.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento do labor em condições insalubres, em razão da exposição ocupacional habitual a calor intenso no setor de fusão da reclamada, com condenação da reclamada ao pagamento do adicional de insalubridade em grau a ser definido por prova técnica, observados os parâmetros legais, regulamentares e periciais aplicáveis.",
                "II. A condenação da reclamada ao pagamento das diferenças de adicional de insalubridade relativas ao período contratual indicado na narrativa fática, ou outro período que vier a ser confirmado nos autos, com apuração em liquidação de sentença.",
                "III. De forma subsidiária, caso a prova técnica conclua pelo enquadramento da atividade em situação de risco acentuado juridicamente caracterizável como perigosa, requer o reconhecimento do direito ao adicional de periculosidade, observada a impossibilidade de cumulação automática entre os adicionais de insalubridade e periculosidade, com adoção do adicional cabível ou mais favorável, conforme validação judicial e profissional.",
                "IV. A condenação da reclamada ao pagamento dos reflexos do adicional eventualmente reconhecido em férias acrescidas de 1/3, 13º salário, FGTS, aviso-prévio, quando cabível, e demais verbas trabalhistas de natureza salarial que sejam juridicamente aplicáveis ao caso concreto.",
                "V. A determinação de realização de perícia técnica no ambiente de trabalho, ou por meio técnico equivalente caso inviável a inspeção direta, a fim de apurar a exposição ocupacional ao calor, a intensidade e habitualidade da exposição, a proximidade das fontes térmicas, a existência de pausas, a taxa metabólica da atividade, as condições reais do setor de fusão e a eventual neutralização do agente nocivo por equipamentos de proteção.",
                "VI. A intimação da reclamada para apresentar todos os documentos ambientais, ocupacionais e trabalhistas relacionados ao período contratual, especialmente PPP, LTCAT, PGR, PCMSO, mapa de riscos, laudos ambientais, fichas de entrega de EPI, certificados de aprovação dos equipamentos fornecidos, registros de treinamento, registros de fiscalização de uso de EPI, holerites, contrato de trabalho, controles de jornada e demais documentos necessários à completa elucidação dos fatos.",
                "VII. O reconhecimento de que a simples apresentação de fichas de entrega de EPI não comprova, por si só, a efetiva neutralização do agente nocivo, devendo ser analisadas a adequação, certificação, regularidade de entrega, substituição, fiscalização, treinamento e eficácia real dos equipamentos nas condições concretas de trabalho.",
                "VIII. A autorização para produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, pericial técnica e demais provas que se fizerem necessárias durante a instrução processual.",
                "IX. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, na forma definida pela legislação e pela jurisprudência vigente no momento da liquidação.",
                "X. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "XI. A atribuição à causa de valor provisório a ser definido pelo advogado responsável, com possibilidade de posterior adequação após apresentação de cálculo trabalhista, documentos complementares e conclusão da prova técnica.",
                "XII. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, reconhecendo-se o direito do reclamante ao adicional cabível e às respectivas diferenças e reflexos trabalhistas.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, pericial técnica e demais provas que se fizerem necessárias no curso da instrução.",
                "Requer, de forma específica, a realização de perícia técnica no ambiente de trabalho, ou por meio técnico equivalente caso a inspeção direta se torne inviável, a fim de apurar as condições reais de trabalho no setor de fusão da reclamada, especialmente quanto à exposição ocupacional ao calor, proximidade de fontes térmicas, habitualidade da exposição, intensidade do agente, existência de pausas, taxa metabólica da atividade, medidas de controle adotadas e eventual neutralização por equipamentos de proteção.",
                "Requer que a perícia avalie, de forma expressa, se a exposição ocupacional ao calor ultrapassava os limites juridicamente toleráveis, observando os critérios técnicos aplicáveis, inclusive medições ambientais, parâmetros reconhecidos de avaliação térmica, rotina efetiva de trabalho e demais elementos necessários à correta caracterização da condição laboral.",
                "Requer, ainda, que a reclamada seja intimada a apresentar todos os documentos ambientais, ocupacionais e trabalhistas relacionados ao período contratual, especialmente PPP, LTCAT, PGR, PCMSO, mapa de riscos, laudos ambientais, fichas de entrega de EPI, certificados de aprovação dos equipamentos fornecidos, registros de treinamento, registros de fiscalização de uso de EPI, controles de jornada, holerites, contrato de trabalho e demais documentos relacionados à saúde e segurança do trabalho.",
                "Requer que seja analisada a efetiva adequação dos equipamentos de proteção eventualmente fornecidos, considerando não apenas a existência de ficha de entrega, mas também a compatibilidade do equipamento com o agente nocivo, sua certificação, periodicidade de substituição, treinamento, fiscalização de uso e capacidade real de neutralização ou redução da exposição nas condições concretas de trabalho.",
                "Requer a oitiva de testemunhas que possam esclarecer a rotina laboral do reclamante, a frequência da exposição ao calor, a proximidade das fontes térmicas, as condições do setor de fusão, o uso ou não de equipamentos de proteção, a existência de pausas, a fiscalização pela reclamada e demais fatos relevantes à apuração da insalubridade ou, subsidiariamente, da periculosidade.",
                "Requer que eventual ausência, incompletude ou inconsistência dos documentos ambientais e ocupacionais seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Por fim, requer que todas as provas produzidas sejam analisadas em conjunto, a fim de permitir a correta apuração das condições reais de trabalho, do adicional eventualmente devido, dos reflexos trabalhistas cabíveis e dos valores a serem apurados em liquidação, sempre com observância da prova técnica, documental e testemunhal produzida nos autos.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, reconhecendo-se o direito do reclamante ao adicional de insalubridade por exposição ocupacional ao calor, em grau a ser apurado por prova técnica, ou, subsidiariamente, ao adicional de periculosidade, caso constatado enquadramento jurídico próprio, com o pagamento das diferenças correspondentes e respectivos reflexos trabalhistas.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e pericial técnica, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução processual.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares, prova técnica e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )



    # PATCH: labor_verbas_rescisorias_final_text_v1
    if is_trabalhista_verbas_rescisorias:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à cobrança de verbas rescisórias decorrentes de dispensa sem justa causa, conforme os fatos narrados e documentos a serem conferidos nos autos.",
                "Segundo a narrativa apresentada, o reclamante laborou para a reclamada em período aproximado informado no cadastro do caso, exercendo função remunerada, tendo sido dispensado sem justa causa sem o recebimento integral e tempestivo das parcelas rescisórias que afirma serem devidas.",
                "O reclamante alega que não foram pagos, ou foram pagos de forma incompleta, saldo de salário, aviso-prévio, férias vencidas e/ou proporcionais acrescidas de 1/3, 13º salário proporcional, depósitos de FGTS do período contratual e multa rescisória de 40% sobre o FGTS.",
                "Também afirma que não recebeu corretamente as guias para saque do FGTS e habilitação no seguro-desemprego, ou que houve dificuldade para acessar tais direitos em razão de pendências atribuídas à empregadora.",
                "A controvérsia principal consiste em verificar a data exata de admissão e desligamento, a modalidade de rescisão, os valores efetivamente pagos, a regularidade dos depósitos de FGTS, a entrega das guias rescisórias e a existência de diferenças trabalhistas a serem apuradas por cálculo técnico.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de documentos como CTPS ou contrato de trabalho, TRCT, aviso de dispensa, holerites, comprovantes de pagamento, extrato analítico do FGTS, comunicações entre as partes e demais documentos relacionados à rescisão contratual.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da reclamação trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à cobrança de verbas rescisórias decorrentes de dispensa sem justa causa, com apuração documental e cálculo das parcelas efetivamente devidas.",
                "II. Das verbas rescisórias em dispensa sem justa causa. Em regra, a dispensa sem justa causa pode gerar direito ao pagamento de saldo de salário, aviso-prévio, férias vencidas e proporcionais acrescidas de 1/3, 13º salário proporcional, liberação do FGTS, multa rescisória de 40% sobre o FGTS e demais parcelas cabíveis conforme o contrato e a prova documental.",
                "III. Do prazo de pagamento e da multa do art. 477 da CLT. Deverá ser verificado se as verbas rescisórias foram pagas dentro do prazo legal aplicável. Caso constatado atraso ou inadimplemento injustificado, poderá ser analisado o cabimento da multa prevista no art. 477 da CLT, conforme validação profissional e prova dos autos.",
                "IV. Da multa do art. 467 da CLT. Havendo verbas incontroversas não quitadas no momento processual adequado, deverá ser analisado o cabimento da multa prevista no art. 467 da CLT, especialmente quanto às parcelas reconhecidas como devidas e não pagas oportunamente.",
                "V. Do FGTS, multa de 40% e guias rescisórias. A apuração deverá considerar o extrato analítico do FGTS, a regularidade dos depósitos durante o contrato, a incidência da multa rescisória de 40%, bem como eventual necessidade de expedição ou regularização das guias para saque do FGTS e habilitação no seguro-desemprego.",
                "VI. Da necessidade de prova documental e cálculo trabalhista. A conclusão sobre valores depende da conferência de CTPS, contrato, TRCT, holerites, comprovantes de pagamento, extrato de FGTS, aviso de dispensa e demais documentos rescisórios, além de cálculo trabalhista preliminar revisado pelo advogado responsável.",
                "VII. Da síntese da tese. A pretensão deve ser conduzida com cautela técnica, evitando promessa de resultado e condicionando a liquidação dos valores à prova documental, à memória de cálculo e à validação profissional antes do protocolo definitivo.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento da dispensa sem justa causa, caso confirmada pela documentação trabalhista e rescisória, com a condenação da reclamada ao pagamento das verbas rescisórias devidas e não quitadas, ou quitadas de forma incompleta.",
                "II. A condenação da reclamada ao pagamento de saldo de salário eventualmente devido, conforme dias trabalhados no mês da rescisão e apuração em cálculo trabalhista.",
                "III. A condenação da reclamada ao pagamento de aviso-prévio indenizado ou diferenças de aviso-prévio, conforme modalidade de cumprimento, tempo de serviço e documentos rescisórios.",
                "IV. A condenação da reclamada ao pagamento de férias vencidas e/ou proporcionais acrescidas de 1/3 constitucional, conforme período aquisitivo, período proporcional e valores já eventualmente pagos.",
                "V. A condenação da reclamada ao pagamento de 13º salário proporcional e eventuais diferenças, conforme período trabalhado no ano da rescisão.",
                "VI. A condenação da reclamada ao recolhimento ou pagamento das diferenças de FGTS do período contratual, com apresentação do extrato analítico e confrontação com os salários pagos.",
                "VII. A condenação da reclamada ao pagamento da multa rescisória de 40% sobre o FGTS devido, caso confirmada a dispensa sem justa causa e constatada ausência ou insuficiência de pagamento.",
                "VIII. A condenação da reclamada à entrega, regularização ou indenização substitutiva das guias necessárias ao saque do FGTS e à habilitação no seguro-desemprego, quando cabível e conforme prova documental.",
                "IX. A condenação da reclamada ao pagamento da multa prevista no art. 477 da CLT, caso comprovado atraso ou ausência de pagamento tempestivo das verbas rescisórias no prazo legal.",
                "X. A aplicação da multa prevista no art. 467 da CLT sobre verbas incontroversas, caso existentes e não quitadas no momento processual adequado.",
                "XI. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, conforme critérios definidos na fase própria.",
                "XII. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "XIII. A produção de todos os meios de prova em direito admitidos, especialmente documental, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outros meios necessários à completa apuração dos fatos.",
                "XIV. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, com apuração dos valores em liquidação ou mediante cálculo trabalhista revisado.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, depoimento pessoal da reclamada e demais provas que se fizerem necessárias durante a instrução.",
                "Requer a juntada e análise de CTPS ou contrato de trabalho, termo de rescisão do contrato de trabalho, aviso de dispensa, holerites, comprovantes de pagamento, extrato analítico do FGTS, guias rescisórias, comunicações entre as partes e demais documentos relacionados à admissão, remuneração, jornada e rescisão contratual.",
                "Requer que a reclamada seja intimada a apresentar documentos rescisórios e trabalhistas sob sua guarda, especialmente TRCT, recibos de pagamento, comprovantes de depósito de FGTS, comprovantes de entrega de guias, registros funcionais, ficha de empregado e demais documentos necessários à conferência das parcelas postuladas.",
                "Requer que seja promovido cálculo trabalhista, ainda que preliminar, para apurar saldo de salário, aviso-prévio, férias vencidas e/ou proporcionais acrescidas de 1/3, 13º salário proporcional, FGTS, multa de 40%, multas legais eventualmente cabíveis, juros e correção monetária.",
                "Requer a oitiva de testemunhas, caso necessário, para esclarecer a modalidade da dispensa, a data de desligamento, a entrega de documentos rescisórios, pagamentos realizados e demais circunstâncias relevantes à controvérsia.",
                "Requer que eventual ausência, incompletude ou inconsistência dos documentos rescisórios seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Por fim, requer que todas as provas sejam analisadas em conjunto, a fim de permitir a correta apuração das verbas rescisórias, das diferenças de FGTS, das guias devidas e das multas legais eventualmente aplicáveis.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, condenando-se a reclamada ao pagamento das verbas rescisórias devidas, diferenças de FGTS, multa de 40%, guias rescisórias, multas legais eventualmente cabíveis e demais parcelas reconhecidas nos autos.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )


    # PATCH: labor_horas_extras_final_text_v1
    if is_trabalhista_horas_extras:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à cobrança de horas extras, reflexos trabalhistas e eventuais diferenças decorrentes de jornada excedente e intervalo intrajornada irregular.",
                "Segundo a narrativa apresentada, o reclamante afirma ter laborado em jornada habitual superior à contratual, com início das atividades por volta das 7h e encerramento por volta das 19h, de segunda a sábado, em rotina que teria extrapolado a jornada ordinária.",
                "O reclamante também sustenta que o intervalo para refeição e descanso era frequentemente reduzido ou não concedido integralmente, circunstância que deverá ser apurada por meio de controles de ponto, escalas, mensagens, ordens de serviço, holerites e prova testemunhal.",
                "Alega, ainda, que parte das horas extras realizadas não era registrada corretamente nos controles de ponto, ou era registrada apenas parcialmente, sem o pagamento integral do adicional de horas extras e dos reflexos trabalhistas correspondentes.",
                "A controvérsia principal consiste em verificar a jornada contratual, a jornada efetivamente cumprida, a fidelidade dos controles de ponto, a regularidade do intervalo intrajornada, os pagamentos realizados e a existência de diferenças de horas extras a serem apuradas por cálculo trabalhista.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de documentos como contrato de trabalho ou CTPS, holerites, controles de ponto, escalas, recibos de pagamento, mensagens, ordens de serviço e demais elementos capazes de demonstrar a rotina real de trabalho.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da reclamação trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à cobrança de horas extras, diferenças de jornada, intervalo intrajornada e reflexos trabalhistas, conforme prova documental, testemunhal e cálculo técnico.",
                "II. Da jornada excedente e das horas extras. Caso comprovado que o reclamante laborava além da jornada legal ou contratual sem a correspondente quitação, serão devidas as diferenças de horas extras, com adicional legal, convencional ou contratual aplicável, observada a jornada efetivamente comprovada.",
                "III. Dos controles de ponto e da prova da jornada. A apuração da jornada depende da análise dos controles de ponto, escalas, holerites, recibos de pagamento, mensagens, ordens de serviço e prova testemunhal. Caso os controles sejam ausentes, incompletos ou incompatíveis com a realidade laboral, a prova deverá ser valorada em conjunto.",
                "IV. Do intervalo intrajornada. Havendo supressão ou concessão parcial do intervalo para refeição e descanso, deverá ser analisado o direito ao pagamento correspondente ao período irregular, conforme legislação trabalhista aplicável, prova da rotina e parâmetros de cálculo definidos na fase própria.",
                "V. Dos reflexos trabalhistas. As horas extras habitualmente prestadas podem gerar reflexos em descanso semanal remunerado, férias acrescidas de 1/3, 13º salário, FGTS e demais parcelas juridicamente cabíveis, conforme habitualidade, base de cálculo e prova dos autos.",
                "VI. Da necessidade de cálculo trabalhista. A quantificação das diferenças depende de cálculo técnico, com confrontação entre jornada alegada, cartões de ponto, holerites, valores pagos, adicionais aplicáveis, compensações eventualmente existentes e reflexos legais.",
                "VII. Da síntese da tese. A pretensão deve ser conduzida com cautela técnica, sem promessa de resultado judicial, condicionando a liquidação dos valores à prova documental, testemunhal, memória de cálculo e validação profissional antes do protocolo definitivo.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento da jornada extraordinária efetivamente prestada, conforme prova documental, controles de ponto, prova testemunhal e demais elementos produzidos nos autos.",
                "II. A condenação da reclamada ao pagamento das horas extras laboradas além da jornada legal ou contratual, com o adicional legal, convencional ou contratual aplicável, conforme apuração em cálculo trabalhista.",
                "III. A condenação da reclamada ao pagamento de diferenças de horas extras eventualmente quitadas a menor, mediante confronto entre controles de ponto, holerites, recibos e jornada efetivamente comprovada.",
                "IV. A condenação da reclamada ao pagamento do período correspondente ao intervalo intrajornada suprimido ou concedido parcialmente, quando comprovada a irregularidade, com os reflexos cabíveis conforme legislação aplicável.",
                "V. A condenação da reclamada ao pagamento dos reflexos das horas extras e diferenças reconhecidas em descanso semanal remunerado, férias acrescidas de 1/3, 13º salário, FGTS e demais verbas trabalhistas juridicamente cabíveis.",
                "VI. A intimação da reclamada para apresentar controles de ponto, escalas de trabalho, registros de jornada, holerites, recibos de pagamento de horas extras, acordos de compensação ou banco de horas, caso existentes, e demais documentos relacionados à jornada do reclamante.",
                "VII. O reconhecimento da invalidade ou insuficiência dos controles de ponto, caso sejam apresentados registros incompatíveis com a jornada efetivamente praticada, britânicos, incompletos ou sem correspondência com a realidade laboral, conforme prova produzida.",
                "VIII. A produção de prova testemunhal para confirmação da jornada real, frequência das horas extras, rotina de intervalos, metas operacionais, fechamento de rotas e demais circunstâncias relevantes.",
                "IX. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, conforme critérios definidos na fase própria.",
                "X. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "XI. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, com apuração dos valores em liquidação ou mediante cálculo trabalhista revisado.",
            ]
        )

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal, depoimento pessoal da reclamada e demais provas necessárias à apuração da jornada efetivamente cumprida.",
                "Requer a juntada e análise de contrato de trabalho ou CTPS, holerites, controles de ponto, cartões de ponto, escalas de trabalho, recibos de pagamento de horas extras, registros de banco de horas, acordos de compensação, mensagens, ordens de serviço, relatórios de rota, registros de metas e demais documentos relacionados à jornada.",
                "Requer que a reclamada seja intimada a apresentar todos os controles de jornada do período contratual discutido, inclusive espelhos de ponto, registros eletrônicos, escalas, recibos de pagamento e documentos relativos a banco de horas ou compensação de jornada.",
                "Requer que seja promovido cálculo trabalhista, ainda que preliminar, para apurar horas extras, adicional aplicável, intervalo intrajornada, reflexos em DSR, férias acrescidas de 1/3, 13º salário, FGTS, juros, correção monetária e compensação de valores eventualmente pagos.",
                "Requer a oitiva de testemunhas que possam esclarecer a jornada real, o horário de entrada e saída, a frequência das horas extras, a regularidade dos intervalos, a existência de metas, carregamento, separação de mercadorias, fechamento de rotas e demais aspectos da rotina laboral.",
                "Requer que eventual ausência, incompletude, inconsistência ou artificialidade dos controles de ponto seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Por fim, requer que todas as provas sejam analisadas em conjunto, a fim de permitir a correta apuração da jornada, das horas extras, dos intervalos irregulares, dos reflexos trabalhistas e dos valores devidos.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, condenando-se a reclamada ao pagamento das horas extras devidas, diferenças de jornada, intervalo intrajornada irregular, reflexos trabalhistas e demais parcelas reconhecidas nos autos.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )


    # PATCH: labor_fgts_nao_recolhido_final_text_v1
    # PATCH: prevent_fgts_template_overriding_severance_v1
    # Casos de verbas rescisórias podem mencionar FGTS/multa de 40% como pedidos acessórios,
    # mas não devem ser roteados para o template principal de FGTS não recolhido.
    if is_trabalhista_fgts_nao_recolhido and not is_trabalhista_verbas_rescisorias:
        resumo_fatico = _paragraphs(
            [
                f"Trata-se de reclamação trabalhista relacionada ao caso {case.case_number} — {case.title}, voltada à cobrança, regularização ou indenização de depósitos de FGTS não recolhidos, recolhidos parcialmente ou realizados de forma irregular durante o contrato de trabalho.",
                "Segundo a narrativa apresentada, o reclamante afirma que, ao consultar o extrato analítico da conta vinculada do FGTS, identificou ausência de depósitos em determinados meses do contrato, valores inferiores aos devidos ou períodos sem movimentação compatível com a remuneração recebida.",
                "O reclamante sustenta que a irregularidade no recolhimento do FGTS prejudicou a formação do saldo fundiário e a regularidade das obrigações trabalhistas da empregadora, sendo necessária a conferência mês a mês entre remuneração, holerites, extrato analítico e comprovantes de recolhimento.",
                "De forma subsidiária ou condicionada, caso confirmada dispensa sem justa causa, deverá ser analisada eventual diferença na multa rescisória de 40% sobre o FGTS, limitada ao saldo e às diferenças efetivamente reconhecidas.",
                "A controvérsia principal consiste em verificar se houve ausência total ou parcial de depósitos de FGTS, se os valores recolhidos correspondem à remuneração mensal devida, quais competências apresentam inconsistência e se há diferenças a serem recolhidas, regularizadas ou indenizadas.",
                "Para adequada apuração dos fatos, mostra-se necessária a análise de CTPS ou contrato de trabalho, holerites, extrato analítico completo do FGTS, comprovantes de pagamento salarial, documentos rescisórios, GFIP, SEFIP, eSocial, comprovantes de recolhimento e demais documentos sob guarda da empregadora.",
            ]
        )

        fundamentacao = _paragraphs(
            [
                "I. Do cabimento da reclamação trabalhista. À luz do quadro fático narrado, a demanda deve ser estruturada como reclamação trabalhista voltada à apuração de depósitos de FGTS não recolhidos, recolhidos parcialmente ou realizados de forma irregular durante o contrato de trabalho.",
                "II. Da obrigação de recolhimento do FGTS. O empregador possui dever de realizar os depósitos fundiários incidentes sobre a remuneração do empregado, cabendo apurar, por documentos e cálculo técnico, se houve regularidade dos recolhimentos durante todo o período contratual discutido.",
                "III. Das diferenças de FGTS. A existência de diferenças deve ser verificada mediante confronto entre extrato analítico da conta vinculada, holerites, remuneração mensal, comprovantes de recolhimento, documentos fiscais/trabalhistas e demais registros apresentados pelas partes.",
                "IV. Da exibição documental. Considerando que documentos como GFIP, SEFIP, eSocial, comprovantes de recolhimento, fichas financeiras e registros funcionais podem estar sob guarda da reclamada, mostra-se cabível requerer sua apresentação para completa apuração das competências e valores devidos.",
                "V. Da multa rescisória de 40%, se cabível. A multa de 40% sobre o FGTS somente deverá ser analisada caso confirmada a modalidade rescisória que a autorize, especialmente dispensa sem justa causa, e deverá incidir sobre o saldo e diferenças efetivamente reconhecidos, conforme cálculo trabalhista.",
                "VI. Da necessidade de cálculo trabalhista. A quantificação depende de cálculo mês a mês, com apuração das competências sem recolhimento, valores recolhidos a menor, base remuneratória, atualização, juros e eventual repercussão na multa rescisória, quando cabível.",
                "VII. Da síntese da tese. A pretensão deve ser conduzida com cautela técnica, sem promessa de resultado judicial, condicionando a conclusão à prova documental, ao extrato analítico completo, à exibição de documentos pela reclamada e à validação profissional antes do protocolo definitivo.",
            ]
        )

        pedidos = _paragraphs(
            [
                "Diante do exposto, requer o reclamante:",
                "I. O reconhecimento da existência de ausência, insuficiência ou irregularidade nos depósitos de FGTS durante o contrato de trabalho, conforme apuração documental e cálculo trabalhista.",
                "II. A condenação da reclamada ao recolhimento, regularização ou pagamento indenizado das diferenças de FGTS devidas no período contratual, conforme competências apuradas e valores identificados no extrato analítico da conta vinculada.",
                "III. A determinação para que a reclamada apresente comprovantes de recolhimento de FGTS, GFIP, SEFIP, eSocial, fichas financeiras, registros funcionais, holerites, recibos salariais e demais documentos necessários à conferência das competências discutidas.",
                "IV. A condenação da reclamada ao pagamento das diferenças de FGTS apuradas mês a mês, considerando a remuneração devida, verbas salariais integrantes da base de cálculo e valores já eventualmente recolhidos.",
                "V. Caso confirmada dispensa sem justa causa ou hipótese legal equivalente, a condenação da reclamada ao pagamento das diferenças da multa rescisória de 40% sobre o FGTS, calculada sobre o saldo e as diferenças reconhecidas.",
                "VI. A regularização da conta vinculada do FGTS do reclamante, quando tecnicamente possível, ou, subsidiariamente, o pagamento indenizado das diferenças correspondentes.",
                "VII. A produção de prova documental, contábil, testemunhal e demais meios de prova admitidos em direito, especialmente para apuração da remuneração, das competências sem recolhimento e dos valores devidos.",
                "VIII. A condenação da reclamada ao pagamento das parcelas deferidas com juros, correção monetária e demais acréscimos legais aplicáveis, conforme critérios definidos na fase própria.",
                "IX. A condenação da reclamada ao pagamento de honorários advocatícios sucumbenciais, nos termos da legislação trabalhista aplicável.",
                "X. Ao final, requer a procedência dos pedidos, nos limites da prova produzida, com apuração dos valores em liquidação ou mediante cálculo trabalhista revisado.",
            ]
        )

        pedidos_valores_estimados, calculated_cause_value = _build_fgts_claim_values_section(
            state_metadata,
            case,
            cause_value,
        )
        if calculated_cause_value:
            cause_value = calculated_cause_value

        provas_requerimentos = _paragraphs(
            [
                "Requer o reclamante a produção de todos os meios de prova em direito admitidos, especialmente prova documental, contábil, testemunhal, depoimento pessoal da reclamada e demais provas necessárias à apuração da regularidade dos depósitos de FGTS.",
                "Requer a juntada e análise de CTPS ou contrato de trabalho, holerites, comprovantes de pagamento salarial, extrato analítico completo do FGTS, termo de rescisão, quando houver, comprovantes de recolhimento, GFIP, SEFIP, eSocial, fichas financeiras e demais documentos relacionados à remuneração e aos recolhimentos fundiários.",
                "Requer que a reclamada seja intimada a apresentar todos os documentos sob sua guarda relacionados ao FGTS, inclusive comprovantes de recolhimento por competência, GFIP, SEFIP, eSocial, fichas financeiras, folhas de pagamento, registros funcionais e demais documentos necessários à conferência dos depósitos.",
                "Requer que seja promovido cálculo trabalhista, ainda que preliminar, para apurar competências sem recolhimento, depósitos realizados a menor, base remuneratória, atualização, juros e eventual diferença de multa rescisória de 40%, se cabível.",
                "Requer que eventual ausência, incompletude ou inconsistência dos comprovantes de recolhimento seja considerada na valoração da prova, especialmente quando tais documentos estiverem sob guarda ou responsabilidade da reclamada.",
                "Requer a oitiva de testemunhas, caso necessário, para esclarecer a rotina contratual, remuneração, comunicações internas sobre FGTS e demais fatos relevantes, sem prejuízo da prioridade da prova documental e contábil.",
                "Por fim, requer que todas as provas sejam analisadas em conjunto, a fim de permitir a correta apuração das diferenças de FGTS, da regularização da conta vinculada, dos valores indenizáveis e das parcelas acessórias eventualmente cabíveis.",
            ]
        )

        fechamento = _paragraphs(
            [
                "Diante de todo o exposto, requer o reclamante o regular processamento da presente reclamação trabalhista, com a citação da reclamada para, querendo, apresentar defesa, sob pena de revelia e confissão quanto à matéria de fato, na forma da legislação aplicável.",
                "Requer, ao final, sejam julgados procedentes os pedidos formulados, condenando-se a reclamada ao recolhimento, regularização ou pagamento indenizado das diferenças de FGTS devidas, bem como à diferença da multa rescisória de 40%, caso cabível e comprovada a hipótese legal correspondente.",
                "Requer, ainda, a produção de todos os meios de prova em direito admitidos, especialmente prova documental, contábil, testemunhal e depoimento pessoal da reclamada, sem prejuízo de outras provas que se mostrarem necessárias no curso da instrução.",
                f"Dá-se à causa o valor provisório de R$ {cause_value}, sujeito a posterior adequação conforme memória de cálculo, documentos complementares e liquidação dos pedidos.",
                f"Por fim, requer que todas as intimações e publicações sejam realizadas em nome de {lawyer_name}, inscrito na OAB/{lawyer_uf} sob o nº {lawyer_oab}, sob pena de nulidade, caso aplicável.",
                "Termos em que,",
                "Pede deferimento.",
                f"{signature_local}, {signature_date}.",
                f"{lawyer_name}\nOAB/{lawyer_uf} {lawyer_oab}",
            ]
        )

    protocolo_checklist = _build_protocol_readiness_checklist_section(
        author_inline_qualification=author_inline_qualification,
        defendant_inline_qualification=defendant_inline_qualification,
        lawyer_name=lawyer_name,
        lawyer_oab=lawyer_oab,
        lawyer_uf=lawyer_uf,
        signature_local=signature_local,
        signature_date=signature_date,
        cause_value=cause_value,
        is_fgts_case=is_trabalhista_fgts_nao_recolhido and not is_trabalhista_verbas_rescisorias,
    )

    return [
        {
            "key": "enderecamento",
            "title": "Endereçamento",
            "content": enderecamento,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "qualificacao_partes",
            "title": "Qualificação das Partes",
            "content": qualificacao_partes,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
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
        {
            "key": "pedidos_valores_estimados",
            "title": "Pedidos e Valores Estimados",
            "content": pedidos_valores_estimados,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "calculation", "strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "requires_professional_review",
            },
        },
        {
            "key": "provas_requerimentos",
            "title": "Provas e Requerimentos",
            "content": provas_requerimentos,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["technical_analysis", "strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "fechamento",
            "title": "Fechamento",
            "content": fechamento,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["strategy"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "ok",
            },
        },
        {
            "key": "checklist_final_protocolo",
            "title": "Checklist Final para Protocolo",
            "content": protocolo_checklist,
            "source": "assisted_draft",
            "status": "draft",
            "metadata": {
                "origin_sources": ["case", "calculation", "strategy", "protocol_readiness"],
                "generation_mode": "assisted_draft_from_analysis",
                "guardrail_status": "requires_professional_review",
                "export_visibility": "internal",
                "include_in_final_pdf": False,
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
            "title": _resolve_editor_export_title(db, document, current_user["tenant_id"]),
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
            "title": _resolve_editor_export_title(db, document, current_user["tenant_id"]),
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
    assisted_sections = _build_assisted_sections(
        db,
        case,
        analysis_record,
        current_user["tenant_id"],
        document_metadata=document.document_metadata or {},
    )

    current_user_id = _resolve_current_user_id(db, current_user)
    next_version_number = document.current_version_number + 1

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=next_version_number,
        approved=False,
        notes="Peça pronta gerada a partir da análise do caso",
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
