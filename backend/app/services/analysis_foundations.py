from __future__ import annotations

from typing import Any


def _base_normativa_for_area(legal_area: str | None) -> list[str]:
    area = (legal_area or "").strip().lower()

    if area == "civil_ambiental":
        return [
            "Código Civil, arts. 186, 187 e 927 — responsabilidade civil por ato ilícito e abuso de direito.",
            "Código Civil, art. 1.277 — direito de vizinhança, sossego, saúde e segurança.",
            "Código de Processo Civil, arts. 300, 497 e 537 — tutela de urgência, obrigação de fazer/não fazer e astreintes.",
            "Constituição Federal, art. 225 — proteção ao meio ambiente ecologicamente equilibrado.",
            "Lei 10.741/2003 (Estatuto do Idoso) — prioridade e proteção reforçada à pessoa idosa.",
            "Lei 9.605/1998 — reforço normativo ambiental quando houver poluição com potencial dano à saúde.",
        ]

    if area == "trabalhista":
        return [
            "CLT — normas gerais de proteção ao trabalho e deveres do empregador.",
            "Constituição Federal, art. 7º — direitos sociais do trabalhador.",
            "Código de Processo Civil aplicado subsidiariamente — tutela de urgência e produção probatória.",
        ]

    return [
        "Constituição Federal — devido processo legal, acesso à justiça e proteção de direitos fundamentais.",
        "Código de Processo Civil — tutela de urgência, produção de prova e técnicas executivas.",
        "Responsabilidade civil e legislação material aplicável conforme a área jurídica informada.",
    ]


def _elementos_faticos(case: dict[str, Any], technical: dict[str, Any]) -> list[str]:
    description = str(case.get("description") or "").lower()
    summary = str(technical.get("summary") or "")
    elements: list[str] = []

    keyword_map = [
        ("poeira", "Relato de emissão de poeira/material particulado no imóvel vizinho."),
        ("cimento", "Indicação de poeira de cimento associada à atividade industrial da parte ré."),
        ("ruído", "Relato de ruído contínuo com impacto no sossego e no repouso."),
        ("barulho", "Relato de perturbação sonora associada à atividade da ré."),
        ("visibilidade", "Relato de obstrução de visibilidade e interferência na segurança da via."),
        ("veículos", "Relato de veículos/materiais posicionados de forma potencialmente lesiva à segurança."),
        ("muro", "Relato de ausência de muro/barreira física entre os imóveis."),
        ("barreira", "Relato de ausência de barreira física de contenção."),
        ("idosa", "Presença de pessoa idosa entre os afetados pelo caso."),
        ("pulmon", "Indicação de problema pulmonar relevante para urgência e nexo de dano."),
        ("notificação", "Existência de tentativa prévia extrajudicial narrada no caso."),
        ("extrajudicial", "Tentativa extrajudicial prévia considerada na leitura estratégica."),
    ]

    for key, label in keyword_map:
        if key in description and label not in elements:
            elements.append(label)

    if summary and "tutela de urgência" in summary.lower():
        elements.append("A análise técnica identificou plausibilidade de tutela de urgência conforme os fatos narrados.")

    if not elements:
        elements.append("Foram considerados os fatos narrados no cadastro do caso e na síntese técnica consolidada.")

    return elements[:6]


def _lacunas_probatorias(technical: dict[str, Any]) -> list[str]:
    issues = [str(item).strip() for item in (technical.get("issues") or []) if str(item).strip()]
    next_steps = [str(item).strip() for item in (technical.get("next_steps") or []) if str(item).strip()]
    combined = " ".join([*issues, *next_steps]).lower()

    gaps: list[str] = []

    gap_rules = [
        (("laudo", "médic", "medic"), "Necessidade de laudo/relatório médico atualizado para robustecer nexo causal e urgência."),
        (("acúst", "acust"), "Necessidade de prova ou medição acústica do ruído alegado."),
        (("particulado", "poeira", "ambiental"), "Necessidade de prova técnica ambiental sobre poeira/material particulado."),
        (("foto", "vídeo", "video"), "Necessidade de prova visual datada (fotos/vídeos) para reforçar materialidade dos fatos."),
        (("notificação", "notificacao"), "Necessidade de comprovar documentalmente a notificação extrajudicial e seu recebimento."),
        (("data", "datas"), "Necessidade de cronologia objetiva dos fatos e da persistência da conduta."),
        (("perícia", "pericia"), "Necessidade de perícia técnica para quantificação e correlação dos impactos alegados."),
    ]

    for keys, label in gap_rules:
        if any(key in combined for key in keys) and label not in gaps:
            gaps.append(label)

    if not gaps and issues:
        gaps = issues[:4]

    if not gaps:
        gaps.append("Não há lacunas probatórias relevantes explicitadas no estado atual da análise.")

    return gaps[:6]


def build_analysis_foundations(
    case: dict[str, Any],
    technical: dict[str, Any],
    viability: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    legal_area = case.get("legal_area")
    final_status = str(decision.get("final_status") or "").strip()
    probability_percent = decision.get("probability_percent")

    disclaimer = (
        "Saída estruturada a partir dos fatos informados, base normativa aplicável à área selecionada "
        "e critérios de viabilidade/prova. Recomendável validação profissional final antes do protocolo."
    )

    return {
        "normative_basis": _base_normativa_for_area(str(legal_area or "")),
        "factual_elements_considered": _elementos_faticos(case, technical),
        "probative_gaps": _lacunas_probatorias(technical),
        "analysis_context": {
            "legal_area": legal_area,
            "final_status": final_status,
            "probability_percent": probability_percent,
            "viability_label": viability.get("label"),
        },
        "disclaimer": disclaimer,
    }
