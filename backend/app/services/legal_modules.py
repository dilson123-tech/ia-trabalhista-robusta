from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class LegalModule:
    id: str
    label: str
    canonical_legal_area: str
    status: str
    aliases: tuple[str, ...]
    action_keywords: tuple[str, ...]
    safety_notes: tuple[str, ...]


def _slug(value: str | None) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[/_-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


LEGAL_MODULES: dict[str, LegalModule] = {
    "trabalhista": LegalModule(
        id="trabalhista",
        label="Trabalhista",
        canonical_legal_area="trabalhista",
        status="operational_real_supervised",
        aliases=("trabalhista", "trabalho", "laboral", "direito do trabalho"),
        action_keywords=(
            "reclamacao trabalhista",
            "verbas rescisorias",
            "horas extras",
            "fgts",
            "insalubridade",
            "periculosidade",
            "ctps",
            "vinculo empregaticio",
        ),
        safety_notes=(
            "Exige revisão de datas, prescrição, documentos trabalhistas, cálculos e estratégia pelo advogado.",
        ),
    ),
    "civel": LegalModule(
        id="civel",
        label="Cível",
        canonical_legal_area="civel",
        status="qa_existing",
        aliases=("civel", "civil", "direito civil"),
        action_keywords=(
            "cobranca civil",
            "obrigacao de fazer",
            "indenizacao",
            "dano moral",
            "dano material",
            "tutela de urgencia",
        ),
        safety_notes=(
            "Exige conferência de competência, causa de pedir, prova documental, valores e pedidos.",
        ),
    ),
    "consumidor": LegalModule(
        id="consumidor",
        label="Consumidor",
        canonical_legal_area="consumidor",
        status="qa_existing_to_formalize",
        aliases=("consumidor", "consumerista", "direito do consumidor", "cdc"),
        action_keywords=(
            "produto com defeito",
            "vicio do produto",
            "servico nao prestado",
            "cobranca indevida",
            "negativacao",
            "restituicao",
            "fornecedor",
        ),
        safety_notes=(
            "Exige prova da relação de consumo, fornecedor, pagamento, falha, protocolos e dano alegado.",
        ),
    ),
    "familia": LegalModule(
        id="familia",
        label="Família",
        canonical_legal_area="familia",
        status="qa_existing_to_formalize",
        aliases=("familia", "família", "direito de familia", "vara de familia"),
        action_keywords=(
            "alimentos",
            "guarda",
            "convivencia",
            "divorcio",
            "partilha",
            "menor",
            "melhor interesse",
        ),
        safety_notes=(
            "Exige linguagem sensível, proteção de menores, revisão humana e cuidado com dados familiares.",
        ),
    ),
    "previdenciario": LegalModule(
        id="previdenciario",
        label="Previdenciário / BPC-LOAS",
        canonical_legal_area="previdenciario",
        status="qa_existing_to_formalize",
        aliases=("previdenciario", "previdenciário", "inss", "bpc", "loas", "bpc loas"),
        action_keywords=(
            "bpc",
            "loas",
            "inss",
            "cadunico",
            "cadunico",
            "idoso",
            "pessoa com deficiencia",
            "vulnerabilidade social",
            "beneficio assistencial",
        ),
        safety_notes=(
            "Exige conferência de renda, composição familiar, CadÚnico, documentos médicos/sociais e decisão do INSS.",
        ),
    ),
    "criminal": LegalModule(
        id="criminal",
        label="Criminal",
        canonical_legal_area="criminal",
        status="operational_initial_package",
        aliases=("criminal", "penal", "direito penal", "processo penal"),
        action_keywords=(
            "liberdade provisoria",
            "habeas corpus",
            "relaxamento de prisao",
            "resposta a acusacao",
            "prisao em flagrante",
            "audiencia de custodia",
            "medidas cautelares",
        ),
        safety_notes=(
            "Não prometer resultado, não afirmar culpa/inocência definitiva e exigir revisão por advogado habilitado.",
        ),
    ),
    "civil_ambiental": LegalModule(
        id="civil_ambiental",
        label="Civil/Ambiental",
        canonical_legal_area="civil_ambiental",
        status="qa_existing_to_formalize",
        aliases=("civil ambiental", "civil_ambiental", "ambiental", "direito ambiental", "vizinhanca"),
        action_keywords=(
            "poeira",
            "ruido",
            "vibracao",
            "barreira",
            "poluicao",
            "direito de vizinhanca",
            "dano ambiental",
        ),
        safety_notes=(
            "Exige prova técnica, prova visual, prova ambiental/acústica/médica e revisão do nexo causal.",
        ),
    ),
}


OFFICIAL_LEGAL_MODULE_IDS: tuple[str, ...] = tuple(LEGAL_MODULES.keys())


_ALIAS_TO_MODULE: dict[str, str] = {}
for module_id, module in LEGAL_MODULES.items():
    _ALIAS_TO_MODULE[_slug(module_id)] = module_id
    _ALIAS_TO_MODULE[_slug(module.canonical_legal_area)] = module_id
    for alias in module.aliases:
        _ALIAS_TO_MODULE[_slug(alias)] = module_id


def normalize_legal_area(value: str | None, *, default: str = "trabalhista", strict: bool = False) -> str:
    normalized = _slug(value)
    if not normalized:
        return default

    if normalized in _ALIAS_TO_MODULE:
        return _ALIAS_TO_MODULE[normalized]

    if strict:
        return default

    return normalized.replace(" ", "_")


def infer_legal_module(
    legal_area: str | None = None,
    action_type: str | None = None,
    title: str | None = None,
    description: str | None = None,
    *,
    default: str = "trabalhista",
) -> str:
    explicit = normalize_legal_area(legal_area, default="", strict=True)

    search_text = _slug(" ".join([
        str(action_type or ""),
        str(title or ""),
        str(description or ""),
    ]))

    # Quando o caso chega como cível genérico, tentamos separar o submódulo correto.
    if explicit and explicit not in {"civel"}:
        return explicit

    for module_id, module in LEGAL_MODULES.items():
        if module_id == "civel":
            continue

        for keyword in module.action_keywords:
            if _slug(keyword) in search_text:
                return module_id

    return explicit or default


def get_legal_module_config(module_id: str | None) -> LegalModule:
    normalized = normalize_legal_area(module_id, default="civel", strict=True)
    return LEGAL_MODULES.get(normalized, LEGAL_MODULES["civel"])


def list_legal_modules() -> list[dict]:
    return [
        {
            "id": module.id,
            "label": module.label,
            "canonical_legal_area": module.canonical_legal_area,
            "status": module.status,
            "aliases": list(module.aliases),
            "action_keywords": list(module.action_keywords),
            "safety_notes": list(module.safety_notes),
        }
        for module in LEGAL_MODULES.values()
    ]
