from __future__ import annotations

from datetime import date
import logging
from typing import Any

from app.core.settings import settings
from app.services.llm_client import LLMClientError, request_structured_analysis
from app.services.legal_modules import infer_legal_module, normalize_legal_area

logger = logging.getLogger(__name__)


def _combined_analysis_text(summary: str, issues: list[str], next_steps: list[str]) -> str:
    return " ".join([summary, *issues, *next_steps]).lower()


def _coerce_risk_level(summary: str, issues: list[str], next_steps: list[str], risk_level: str) -> str:
    combined = _combined_analysis_text(summary, issues, next_steps)

    high_fragility_terms = [
        "ausência de prova documental",
        "falta de prova documental",
        "fragilidade probatória",
        "ônus da prova não cumprido",
        "ônus da prova nao cumprido",
        "sentença de improcedência baseada na ausência de prova",
        "sentenca de improcedencia baseada na ausencia de prova",
        "improcedência por ausência de prova",
        "improcedencia por ausencia de prova",
        "ausência de testemunhas",
        "ausencia de testemunhas",
        "falta de datas",
        "faltam datas",
        "não há datas",
        "nao ha datas",
        "não há valores detalhados",
        "nao ha valores detalhados",
        "impossibilidade de fundamentar reflexos",
        "dependência probatória",
        "dependencia probatoria",
    ]

    medium_fragility_terms = [
        "risco prescricional",
        "prescrição",
        "prescricao",
        "impossibilidade de cálculo",
        "impossibilidade de calculo",
        "impede apuração",
        "impede apuracao",
        "impede cálculo",
        "impede calculo",
        "sem documentos",
        "sem testemunhas",
        "prova testemunhal",
        "produção de prova",
        "producao de prova",
        "liquidação",
        "liquidacao",
    ]

    high_hits = sum(1 for term in high_fragility_terms if term in combined)
    medium_hits = sum(1 for term in medium_fragility_terms if term in combined)

    if risk_level == "low":
        if high_hits >= 3:
            return "high"
        if high_hits >= 2 or medium_hits >= 2:
            return "medium"

    if risk_level == "medium":
        if high_hits >= 4 or (high_hits >= 2 and medium_hits >= 3):
            return "high"

    return risk_level



def _assert_area_coherence(legal_area: str, summary: str, issues: list[str], next_steps: list[str]) -> None:
    normalized_area = normalize_legal_area(legal_area or "trabalhista")
    if normalized_area == "trabalhista":
        return

    combined = " ".join([summary, *issues, *next_steps]).lower()
    forbidden_terms = [
        "trabalhista",
        "reclamação trabalhista",
        "reclamacao trabalhista",
        "justiça do trabalho",
        "justica do trabalho",
        "vínculo empregatício",
        "vinculo empregaticio",
        "vínculo de emprego",
        "vinculo de emprego",
        "empregador",
        "contrato de trabalho",
        "fgts",
        "ctps",
        "holerite",
        "holerites",
        "insalubridade",
        "prescrição bienal",
        "prescricao bienal",
        "quinquenal",
    ]
    if normalized_area in {"criminal", "penal"}:
        forbidden_terms.extend(
            [
                "direito de vizinhança",
                "poeira",
                "cimento",
                "material particulado",
                "acústica",
                "acustica",
                "obrigação de fazer",
                "obrigacao de fazer",
                "reclamação cível",
                "reclamacao civel",
            ]
        )

    hits = sorted({term for term in forbidden_terms if term in combined})
    if hits:
        raise LLMClientError(
            f"contaminação de área detectada para '{normalized_area}': {', '.join(hits[:6])}"
        )


def _fallback_analysis(
    case_number: str,
    title: str,
    description: str | None,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> dict[str, Any]:
    normalized_area = infer_legal_module(
        legal_area=legal_area,
        action_type=action_type,
        title=title,
        description=description,
    )
    text = f"{title} {description or ''}".lower()

    issues: list[str] = []
    risk = "low"

    if normalized_area == "trabalhista":
        if "fgts" in text:
            issues.append("Possível ausência de recolhimento de FGTS")
            risk = "medium"

        if "verbas rescisórias" in text or "rescis" in text:
            issues.append("Discussão sobre verbas rescisórias")
            risk = "medium"

        if "horas extras" in text:
            issues.append("Pedido de horas extras")
            risk = "high"

        if len(issues) < 2:
            issues.append("Necessária análise documental detalhada para identificar a controvérsia principal")
            issues.append("Necessário verificar enquadramento jurídico e maturidade probatória do caso")

        next_steps = [
            "Analisar documentos do contrato de trabalho",
            "Verificar documentos rescisórios e comprovantes",
            "Estruturar linha do tempo dos fatos e provas disponíveis",
        ]

    elif normalized_area == "civil_ambiental":
        if any(term in text for term in ["poeira", "cimento", "poluição", "poluicao", "ruído", "ruido", "barulho"]):
            issues.append("Há indícios de interferência nociva compatível com tutela inibitória, obrigação de fazer/não fazer e prova técnica ambiental/acústica")
            risk = "medium"

        if any(term in text for term in ["idosa", "pulmonar", "saúde", "saude"]):
            issues.append("A presença de pessoa idosa e a alegação de comprometimento respiratório reforçam urgência e necessidade de prova médica")
            risk = "medium"

        if any(term in text for term in ["notificação", "notificacao", "extrajudicial"]):
            issues.append("A tentativa prévia extrajudicial pode fortalecer a narrativa de omissão da ré, desde que comprovada documentalmente")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária análise específica de direito de vizinhança, tutela de urgência e responsabilidade civil ambiental")
            issues.append("Necessário consolidar fatos, documentos, prova médica e prova técnica antes de conclusão definitiva")

        next_steps = [
            "Organizar cronologia objetiva dos fatos, da perturbação e das tentativas extrajudiciais já realizadas",
            "Reunir prova visual, médica e técnica mínima sobre poeira, ruído, saúde da autora e obstrução da via",
            "Estruturar estratégia de obrigação de fazer/não fazer com tutela de urgência e eventual pedido indenizatório compatível com a prova disponível",
        ]


    elif normalized_area == "consumidor":
        if any(term in text for term in ["produto", "defeito", "vício", "vicio", "garantia"]):
            issues.append("Possível vício/defeito de produto, exigindo prova da compra, falha apresentada e tentativa de solução com fornecedor")
            risk = "medium"

        if any(term in text for term in ["serviço", "servico", "não prestado", "nao prestado", "falha na prestação", "falha na prestacao"]):
            issues.append("Possível falha na prestação de serviço, dependente de contrato, pagamento, protocolos e prova do descumprimento")
            risk = "medium"

        if any(term in text for term in ["cobrança indevida", "cobranca indevida", "negativação", "negativacao", "restituição", "restituicao"]):
            issues.append("Possível cobrança indevida, negativação ou restituição, exigindo documentos, protocolos e prova do dano")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária análise consumerista específica da relação de consumo, fornecedor, produto/serviço, falha e dano alegado")
            issues.append("Necessário consolidar nota fiscal, contrato, comprovantes, protocolos e tentativas administrativas antes da conclusão")

        next_steps = [
            "Confirmar relação de consumo, fornecedor, produto ou serviço contratado e valores envolvidos",
            "Anexar nota fiscal, contrato, comprovante de pagamento, protocolos de atendimento e registros de reclamação",
            "Organizar cronologia da falha, tentativas de solução e prejuízos suportados",
            "Submeter pedidos de restituição, obrigação de fazer ou indenização à revisão do advogado",
        ]

    elif normalized_area == "familia":
        if any(term in text for term in ["guarda", "convivência", "convivencia", "visita", "menor", "criança", "crianca"]):
            issues.append("Discussão familiar envolvendo guarda, convivência ou interesse de menor, exigindo cuidado probatório e linguagem sensível")
            risk = "medium"

        if any(term in text for term in ["alimentos", "pensão", "pensao", "necessidade", "possibilidade"]):
            issues.append("Possível demanda de alimentos, dependente de prova de necessidade, possibilidade econômica e vínculo familiar")
            risk = "medium"

        if any(term in text for term in ["divórcio", "divorcio", "partilha", "união estável", "uniao estavel"]):
            issues.append("Possível dissolução de vínculo familiar ou partilha, exigindo documentos pessoais, patrimoniais e estratégia consensual/litigiosa")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária triagem de família com qualificação das partes, vínculo familiar, documentos e definição da medida adequada")
            issues.append("Necessário preservar linguagem sensível, dados pessoais e eventual interesse de menores")

        next_steps = [
            "Confirmar vínculo familiar, partes envolvidas, existência de menores e medida pretendida",
            "Anexar documentos pessoais, certidões, comprovantes de renda, despesas e residência conforme o caso",
            "Organizar cronologia objetiva dos fatos e eventuais tentativas de acordo",
            "Submeter estratégia e pedidos à revisão do advogado antes de qualquer uso externo",
        ]

    elif normalized_area == "previdenciario":
        if any(term in text for term in ["bpc", "loas", "benefício assistencial", "beneficio assistencial"]):
            issues.append("Possível BPC/LOAS, exigindo análise de idade/deficiência, vulnerabilidade social, CadÚnico e documentação familiar")
            risk = "medium"

        if any(term in text for term in ["inss", "indeferimento", "administrativo", "requerimento"]):
            issues.append("Necessária conferência do requerimento administrativo, decisão do INSS, prazos e documentos anexados")
            risk = "medium"

        if any(term in text for term in ["idoso", "deficiência", "deficiencia", "laudo", "médico", "medico", "cadúnico", "cadunico", "renda"]):
            issues.append("A prova social, médica e econômica é central para avaliar elegibilidade e estratégia previdenciária/assistencial")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária triagem previdenciária/assistencial com documentos pessoais, sociais, médicos e econômicos")
            issues.append("Necessário validar requisitos legais, prova administrativa e estratégia com advogado")

        next_steps = [
            "Conferir requerimento administrativo, decisão do INSS, CadÚnico e composição familiar",
            "Anexar documentos pessoais, comprovantes de renda, laudos/relatórios médicos e documentos sociais",
            "Organizar linha do tempo do benefício, indeferimento e eventuais recursos administrativos",
            "Submeter tese, pedidos e documentos à revisão do advogado antes do protocolo",
        ]

    elif normalized_area in {"criminal", "penal"}:
        normalized_action = (action_type or "").strip().lower()

        if any(term in text for term in ["prisão", "prisao", "flagrante", "custódia", "custodia"]):
            issues.append("Necessária conferência da legalidade da prisão, comunicação, nota de culpa, auto de prisão e decisão de custódia")
            risk = "high"

        if any(term in text for term in ["liberdade provisória", "liberdade provisoria", "medidas cautelares"]) or "liberdade" in normalized_action:
            issues.append("Possível avaliação de liberdade provisória ou medidas cautelares diversas da prisão, condicionada aos fatos e documentos")
            risk = "high"

        if any(term in text for term in ["relaxamento", "ilegalidade", "prisão ilegal", "prisao ilegal"]) or "relaxamento" in normalized_action:
            issues.append("Possível análise de relaxamento de prisão quando houver ilegalidade formal ou material demonstrável")
            risk = "high"

        if any(term in text for term in ["denúncia", "denuncia", "resposta à acusação", "resposta a acusacao"]) or "resposta" in normalized_action:
            issues.append("Necessária organização da imputação, preliminares, mérito, provas e testemunhas para resposta à acusação")
            risk = "medium"

        if any(term in text for term in ["habeas corpus", "constrangimento ilegal"]) or "habeas" in normalized_action:
            issues.append("Possível avaliação de habeas corpus, com foco em constrangimento ilegal objetivo e urgência")
            risk = "high"

        if len(issues) < 2:
            issues.append("Necessária triagem criminal supervisionada para delimitar fatos, fase procedimental, documentos, provas e riscos urgentes")
            issues.append("Necessário validar estratégia com advogado antes de qualquer uso externo da análise ou minuta")

        next_steps = [
            "Organizar cronologia dos fatos, fase do procedimento, existência de prisão e decisões já proferidas",
            "Conferir boletim de ocorrência, auto de prisão, nota de culpa, denúncia, decisão judicial e demais documentos disponíveis",
            "Mapear provas, testemunhas, registros digitais e pendências documentais sem presumir fatos não informados",
            "Submeter análise e eventual minuta à revisão obrigatória do advogado antes de qualquer protocolo",
        ]

    else:
        if any(term in text for term in ["dano moral", "danos morais", "indenização", "indenizacao"]):
            issues.append("Há indicativo de pretensão indenizatória dependente de demonstração do dano e do nexo causal")
            risk = "medium"

        if any(term in text for term in ["urgência", "urgencia", "liminar", "tutela"]):
            issues.append("Há elementos para avaliar tutela de urgência, condicionada à probabilidade do direito e ao perigo de dano")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária análise jurídica específica da controvérsia conforme a área informada")
            issues.append("Necessário consolidar fatos, documentos e estratégia processual antes de conclusão técnica")

        next_steps = [
            "Organizar linha do tempo dos fatos e das provas disponíveis",
            "Conferir documentos essenciais, notificações e registros relacionados à controvérsia",
            "Definir estratégia processual compatível com a área jurídica informada e com o tipo de ação pretendido",
        ]

    summary = (
        f"Processo {case_number} analisado automaticamente em modo de contingência, "
        f"considerando a área jurídica '{normalized_area}'"
    )
    if action_type:
        summary += f" e o tipo de ação '{action_type}'."
    else:
        summary += "."

    summary += f" Foram identificados {len(issues)} ponto(s) relevante(s)."

    return {
        "summary": summary,
        "risk_level": risk,
        "issues": issues[:6],
        "next_steps": next_steps[:5],
        "analysis_source": "fallback",
        "case_number": case_number,
        "legal_area": normalized_area,
        "action_type": action_type,
    }



def _build_prompt(
    case_number: str,
    title: str,
    description: str | None,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> str:
    today = date.today().isoformat()
    normalized_area = infer_legal_module(
        legal_area=legal_area,
        action_type=action_type,
        title=title,
        description=description,
    )
    action_label = action_type or "Não informado"

    return f"""
    Você é um advogado brasileiro sênior, especializado na área jurídica informada abaixo, com atuação estratégica pré-processual e processual.

    Analise o caso abaixo com rigor técnico. Use apenas os fatos fornecidos. Não invente fatos.
    Se houver falta de informação, deixe isso claro no resumo, nos pontos relevantes e nos próximos passos.
    Considere como data atual da análise: {today}.

    CASO:
    - Área jurídica: {normalized_area}
    - Tipo de ação/medida pretendida: {action_label}
    - Número/identificador: {case_number}
    - Título: {title}
    - Descrição: {description or "Sem descrição fornecida."}

    Retorne exclusivamente um JSON válido, sem markdown, sem comentários e sem texto fora do JSON.

    Formato obrigatório:
    {{
      "summary": "resumo técnico objetivo em português",
      "risk_level": "low|medium|high",
      "issues": ["lista objetiva de pontos jurídicos relevantes"],
      "next_steps": ["lista objetiva de próximos passos recomendados"]
    }}

    Regras obrigatórias:
    - "risk_level" deve ser exatamente "low", "medium" ou "high".
    - "issues" deve ter de 2 a 6 itens.
    - "next_steps" deve ter de 2 a 5 itens.
    - O conteúdo deve variar conforme os fatos do caso.
    - A área jurídica informada é mandatória e deve prevalecer sobre inferências soltas do texto.
    - Quando a área indicada NÃO for trabalhista, é proibido mencionar ou pressupor: reclamação trabalhista, Justiça do Trabalho, vínculo empregatício, empregador, FGTS, CTPS, insalubridade, contrato de trabalho, prescrição bienal trabalhista ou créditos trabalhistas.
    - Se a área for consumidor, priorizar relação de consumo, fornecedor, produto/serviço, defeito/vício, cobrança indevida, protocolos, restituição, obrigação de fazer e dano alegado.
    - Se a área for familia, priorizar vínculo familiar, alimentos, guarda, convivência, divórcio, partilha simples, documentos familiares e melhor interesse da criança quando aplicável.
    - Se a área for previdenciario, priorizar BPC/LOAS, INSS, CadÚnico, renda familiar, laudos/relatórios médicos, vulnerabilidade social, requerimento/indeferimento administrativo e documentos sociais.
    - Se a área for civil_ambiental, priorizar direito de vizinhança, obrigação de fazer/não fazer, tutela de urgência, responsabilidade civil, dano moral, prova ambiental/acústica/médica e proteção à saúde/sossego/segurança.
    - Se a área for criminal ou penal, priorizar triagem criminal, legalidade da prisão, liberdade provisória, relaxamento de prisão, medidas cautelares, resposta à acusação, habeas corpus, provas, testemunhas, prazos e riscos urgentes.
    - Em área criminal ou penal, é proibido prometer resultado, afirmar culpa/inocência de forma definitiva, orientar fuga, ocultação de prova, fraude, intimidação de testemunhas ou qualquer conduta ilegal.
    - Em área criminal ou penal, toda conclusão deve deixar clara a necessidade de revisão e decisão final por advogado habilitado.
    - O resumo deve indicar, quando cabível, se há direito material aparentemente forte, dependência probatória, risco prescricional/decadencial ou necessidade de cálculo.
    - Não usar linguagem vaga sem explicar o motivo técnico.
    - Não inventar documentos, datas, testemunhas ou fatos não descritos.
    - Quando faltarem datas, documentos, medições, laudos, valores ou prova técnica, isso deve aparecer como limitação objetiva da análise.
    - Quando houver pedido de tutela de urgência, avaliar tecnicamente probabilidade do direito e perigo de dano.
    - Se a área for trabalhista, aplicar corretamente as distinções técnicas próprias dessa área, inclusive prescrição bienal quando pertinente.
    - Se a resposta violar a área indicada, ela será descartada.
    """.strip()



def _normalize_analysis(
    payload: dict[str, Any],
    case_number: str,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> dict[str, Any]:
    summary = str(payload.get("summary") or "").strip()
    risk_level = str(payload.get("risk_level") or "").strip().lower()
    issues = payload.get("issues") or []
    next_steps = payload.get("next_steps") or []

    if risk_level not in {"low", "medium", "high"}:
        raise LLMClientError(f"risk_level inválido retornado pelo modelo: {risk_level}")

    if not summary:
        raise LLMClientError("summary vazio retornado pelo modelo")

    if not isinstance(issues, list) or not all(isinstance(item, str) and item.strip() for item in issues):
        raise LLMClientError("issues inválido retornado pelo modelo")

    if not isinstance(next_steps, list) or not all(isinstance(item, str) and item.strip() for item in next_steps):
        raise LLMClientError("next_steps inválido retornado pelo modelo")

    normalized_issues = [str(item).strip() for item in issues][:6]
    normalized_steps = [str(item).strip() for item in next_steps][:5]

    if len(normalized_issues) < 2:
        raise LLMClientError("issues insuficiente retornado pelo modelo")

    if len(normalized_steps) < 2:
        raise LLMClientError("next_steps insuficiente retornado pelo modelo")

    _assert_area_coherence(
        legal_area=legal_area,
        summary=summary,
        issues=normalized_issues,
        next_steps=normalized_steps,
    )

    coerced_risk_level = _coerce_risk_level(
        summary=summary,
        issues=normalized_issues,
        next_steps=normalized_steps,
        risk_level=risk_level,
    )

    return {
        "summary": summary,
        "risk_level": coerced_risk_level,
        "issues": normalized_issues,
        "next_steps": normalized_steps,
        "analysis_source": "llm",
        "case_number": case_number,
        "legal_area": normalize_legal_area(legal_area or "trabalhista"),
        "action_type": action_type,
    }



def analyze_case(
    case_number: str,
    title: str,
    description: str | None,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> dict[str, Any]:
    llm_enabled = bool(getattr(settings, "LLM_ANALYSIS_ENABLED", False))
    effective_legal_area = infer_legal_module(
        legal_area=legal_area,
        action_type=action_type,
        title=title,
        description=description,
    )

    if not llm_enabled:
        return _fallback_analysis(
            case_number=case_number,
            title=title,
            description=description,
            legal_area=effective_legal_area,
            action_type=action_type,
        )

    prompt = _build_prompt(
        case_number=case_number,
        title=title,
        description=description,
        legal_area=legal_area,
        action_type=action_type,
    )

    try:
        payload = request_structured_analysis(prompt)
        return _normalize_analysis(
            payload,
            case_number=case_number,
            legal_area=effective_legal_area,
            action_type=action_type,
        )
    except Exception as exc:
        logger.exception("ai_case_analysis fallback acionado")
        return _fallback_analysis(
            case_number=case_number,
            title=title,
            description=description,
            legal_area=effective_legal_area,
            action_type=action_type,
        )
