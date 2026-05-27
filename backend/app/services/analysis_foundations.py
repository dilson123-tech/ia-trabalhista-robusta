from __future__ import annotations

from typing import Any

from app.services.legal_modules import infer_legal_module


def _base_normativa_for_area(legal_area: str | None) -> list[str]:
    area = infer_legal_module(legal_area=legal_area, default="civel")

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

    if area in {"criminal", "penal"}:
        return [
            "Constituição Federal, art. 5º — devido processo legal, contraditório, ampla defesa, presunção de inocência e controle de legalidade da prisão.",
            "Código de Processo Penal — prisão, liberdade provisória, relaxamento de prisão, medidas cautelares, resposta à acusação e habeas corpus.",
            "Código Penal — tipicidade, ilicitude, culpabilidade e consequências penais conforme os fatos narrados.",
            "Lei 12.403/2011 — medidas cautelares diversas da prisão e parâmetros para avaliação da necessidade da custódia.",
            "Jurisprudência aplicável — controle de fundamentação concreta, contemporaneidade, proporcionalidade e adequação da medida cautelar.",
        ]

    if area == "consumidor":
        return [
            "Código de Defesa do Consumidor — relação de consumo, responsabilidade do fornecedor, vício/defeito do produto ou serviço e práticas abusivas.",
            "Código Civil — responsabilidade civil, perdas e danos e inadimplemento quando aplicável.",
            "Código de Processo Civil — tutela de urgência, produção de prova, inversão do ônus probatório quando cabível e técnicas executivas.",
            "Constituição Federal, art. 5º e art. 170 — acesso à justiça, defesa do consumidor e ordem econômica.",
        ]

    if area == "familia":
        return [
            "Código Civil — direito de família, casamento, união estável, alimentos, guarda e regime de bens conforme o caso.",
            "Estatuto da Criança e do Adolescente — proteção integral e melhor interesse da criança/adolescente quando aplicável.",
            "Código de Processo Civil — ações de família, tutela provisória, prova e autocomposição.",
            "Constituição Federal, art. 226 e 227 — proteção da família, criança e adolescente.",
        ]

    if area == "previdenciario":
        return [
            "Lei 8.742/1993 (LOAS) — benefício de prestação continuada, vulnerabilidade social, idoso e pessoa com deficiência.",
            "Lei 8.213/1991 — benefícios previdenciários e regras gerais quando aplicável.",
            "Decreto 6.214/2007 — regulamentação do BPC/LOAS.",
            "Normas administrativas do INSS — requerimento, indeferimento, recurso e documentação obrigatória.",
            "Código de Processo Civil — prova documental, prova médica/social e tutela de urgência quando cabível.",
        ]

    if area == "civel":
        return [
            "Código Civil — responsabilidade civil, obrigações, inadimplemento contratual e reparação de danos conforme o caso.",
            "Código de Processo Civil — tutela de urgência, produção de prova, obrigação de fazer/não fazer, cobrança e técnicas executivas.",
            "Constituição Federal — devido processo legal, acesso à justiça e proteção de direitos fundamentais.",
        ]

    return [
        "Constituição Federal — devido processo legal, acesso à justiça e proteção de direitos fundamentais.",
        "Código de Processo Civil — tutela de urgência, produção de prova e técnicas executivas.",
        "Responsabilidade civil e legislação material aplicável conforme a área jurídica informada.",
    ]


def _elementos_faticos(case: dict[str, Any], technical: dict[str, Any]) -> list[str]:
    description = str(case.get("description") or "").lower()
    legal_area = infer_legal_module(
        legal_area=case.get("legal_area") or technical.get("legal_area"),
        action_type=case.get("action_type") or technical.get("action_type"),
        title=case.get("title") or technical.get("title"),
        description=case.get("description") or technical.get("summary"),
        default="civel",
    )
    elements: list[str] = []

    def add_when(term: str, label: str) -> None:
        if term in description and label not in elements:
            elements.append(label)

    if legal_area == "civil_ambiental":
        civil_environmental_map = [
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

        for key, label in civil_environmental_map:
            add_when(key, label)

    elif legal_area == "trabalhista":
        labor_map = [
            ("fgts não recolhido", "Relato de possível ausência ou irregularidade nos depósitos de FGTS."),
            ("fgts nao recolhido", "Relato de possível ausência ou irregularidade nos depósitos de FGTS."),
            ("extrato analítico", "Indicação de necessidade de confronto com extrato analítico do FGTS."),
            ("extrato analitico", "Indicação de necessidade de confronto com extrato analítico do FGTS."),
            ("conta vinculada", "Discussão relacionada à regularidade da conta vinculada do FGTS."),
            ("gfip", "Necessidade de conferência de GFIP/SEFIP/eSocial ou comprovantes de recolhimento."),
            ("sefip", "Necessidade de conferência de GFIP/SEFIP/eSocial ou comprovantes de recolhimento."),
            ("esocial", "Necessidade de conferência de GFIP/SEFIP/eSocial ou comprovantes de recolhimento."),
            ("horas extras", "Relato de possível jornada extraordinária não quitada integralmente."),
            ("jornada", "Discussão relacionada à jornada efetivamente cumprida."),
            ("intervalo intrajornada", "Relato de possível irregularidade no intervalo intrajornada."),
            ("controle de ponto", "Necessidade de conferência dos controles de ponto e registros de jornada."),
            ("verbas rescisórias", "Discussão relacionada a verbas rescisórias possivelmente inadimplidas."),
            ("verbas rescisorias", "Discussão relacionada a verbas rescisórias possivelmente inadimplidas."),
            ("dispensa sem justa causa", "Relato de dispensa sem justa causa com possíveis efeitos rescisórios."),
            ("insalubridade", "Discussão relacionada a possível adicional de insalubridade."),
            ("periculosidade", "Discussão relacionada a possível adicional de periculosidade."),
            ("calor", "Relato de possível exposição ocupacional a calor."),
        ]

        for key, label in labor_map:
            add_when(key, label)

    elif legal_area == "consumidor":
        consumer_map = [
            ("produto", "Indicação de produto adquirido, exigindo prova da compra e do defeito/vício alegado."),
            ("defeito", "Relato de defeito ou vício do produto/serviço."),
            ("vício", "Relato de vício do produto/serviço a ser enquadrado no CDC."),
            ("vicio", "Relato de vício do produto/serviço a ser enquadrado no CDC."),
            ("serviço", "Discussão relacionada à prestação de serviço."),
            ("servico", "Discussão relacionada à prestação de serviço."),
            ("fornecedor", "Necessidade de identificar fornecedor e responsabilidade na cadeia de consumo."),
            ("protocolo", "Existência ou necessidade de protocolos de atendimento/reclamação."),
            ("cobrança indevida", "Possível cobrança indevida a ser comprovada documentalmente."),
            ("negativação", "Possível negativação indevida a ser validada por documento/consulta."),
        ]

        for key, label in consumer_map:
            add_when(key, label)

    elif legal_area == "familia":
        family_map = [
            ("alimentos", "Discussão relacionada a alimentos e necessidade/possibilidade econômica."),
            ("pensão", "Discussão relacionada a pensão alimentícia."),
            ("pensao", "Discussão relacionada a pensão alimentícia."),
            ("guarda", "Discussão relacionada à guarda e rotina de cuidado."),
            ("convivência", "Discussão relacionada à convivência familiar."),
            ("convivencia", "Discussão relacionada à convivência familiar."),
            ("divórcio", "Discussão relacionada à dissolução do vínculo conjugal."),
            ("divorcio", "Discussão relacionada à dissolução do vínculo conjugal."),
            ("partilha", "Discussão relacionada à partilha de bens."),
            ("menor", "Presença de menor, exigindo atenção ao melhor interesse da criança/adolescente."),
            ("criança", "Presença de criança/adolescente, exigindo linguagem sensível e prova adequada."),
            ("crianca", "Presença de criança/adolescente, exigindo linguagem sensível e prova adequada."),
        ]

        for key, label in family_map:
            add_when(key, label)

    elif legal_area == "previdenciario":
        previd_map = [
            ("bpc", "Discussão relacionada ao benefício de prestação continuada."),
            ("loas", "Discussão relacionada ao BPC/LOAS e requisitos assistenciais."),
            ("inss", "Existência de eixo administrativo/previdenciário perante o INSS."),
            ("cadúnico", "Necessidade de conferir CadÚnico e composição familiar."),
            ("cadunico", "Necessidade de conferir CadÚnico e composição familiar."),
            ("idoso", "Possível requisito etário para benefício assistencial/previdenciário."),
            ("deficiência", "Possível requisito de deficiência/incapacidade a comprovar por documentação médica/social."),
            ("deficiencia", "Possível requisito de deficiência/incapacidade a comprovar por documentação médica/social."),
            ("renda", "Necessidade de prova de renda familiar e vulnerabilidade social."),
            ("indeferimento", "Necessidade de analisar decisão administrativa de indeferimento."),
            ("laudo", "Necessidade de laudo/relatório médico quando aplicável."),
        ]

        for key, label in previd_map:
            add_when(key, label)

    elif legal_area in {"criminal", "penal"}:
        criminal_map = [
            ("prisão em flagrante", "Relato de prisão em flagrante a ser analisada quanto à legalidade formal e material."),
            ("prisao em flagrante", "Relato de prisão em flagrante a ser analisada quanto à legalidade formal e material."),
            ("flagrante", "Menção a flagrante, exigindo conferência do auto, nota de culpa, comunicação e audiência de custódia."),
            ("liberdade provisória", "Discussão relacionada à possibilidade de liberdade provisória e medidas cautelares diversas da prisão."),
            ("liberdade provisoria", "Discussão relacionada à possibilidade de liberdade provisória e medidas cautelares diversas da prisão."),
            ("relaxamento de prisão", "Possível análise de ilegalidade da prisão e cabimento de relaxamento, conforme revisão do advogado."),
            ("relaxamento de prisao", "Possível análise de ilegalidade da prisão e cabimento de relaxamento, conforme revisão do advogado."),
            ("habeas corpus", "Possível constrangimento ilegal a ser avaliado com cautela para eventual habeas corpus."),
            ("denúncia", "Existência ou expectativa de denúncia, exigindo organização de imputação, fatos, provas e teses defensivas."),
            ("denuncia", "Existência ou expectativa de denúncia, exigindo organização de imputação, fatos, provas e teses defensivas."),
            ("resposta à acusação", "Discussão relacionada à fase de resposta à acusação, preliminares, mérito, provas e testemunhas."),
            ("resposta a acusacao", "Discussão relacionada à fase de resposta à acusação, preliminares, mérito, provas e testemunhas."),
            ("audiência de custódia", "Menção à audiência de custódia, exigindo conferência de legalidade, necessidade da prisão e cautelares."),
            ("audiencia de custodia", "Menção à audiência de custódia, exigindo conferência de legalidade, necessidade da prisão e cautelares."),
            ("medidas cautelares", "Possibilidade de avaliação de medidas cautelares diversas da prisão."),
            ("testemunha", "Indicação de testemunha(s), exigindo organização da prova oral e coerência com a versão defensiva."),
        ]

        for key, label in criminal_map:
            add_when(key, label)

    else:
        generic_map = [
            ("contrato", "Existência de relação contratual narrada no caso."),
            ("pagamento", "Discussão relacionada a pagamentos, valores ou inadimplemento."),
            ("notificação", "Existência de tentativa prévia extrajudicial narrada no caso."),
            ("extrajudicial", "Tentativa extrajudicial prévia considerada na leitura estratégica."),
        ]

        for key, label in generic_map:
            add_when(key, label)

    summary = str(technical.get("summary") or "")
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
        (("prisão", "prisao", "flagrante"), "Necessidade de conferir auto de prisão, nota de culpa, comunicação da prisão e decisão de custódia."),
        (("liberdade provisória", "liberdade provisoria", "cautelar"), "Necessidade de avaliar elementos concretos para liberdade provisória ou medidas cautelares diversas da prisão."),
        (("denúncia", "denuncia", "acusação", "acusacao"), "Necessidade de confrontar a imputação com denúncia, documentos, provas disponíveis e linha defensiva."),
        (("habeas corpus", "constrangimento ilegal"), "Necessidade de demonstrar objetivamente o constrangimento ilegal e a urgência da medida."),
        (("testemunha", "testemunhas"), "Necessidade de qualificar testemunhas e organizar a pertinência da prova oral."),
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
    legal_area = infer_legal_module(
        legal_area=case.get("legal_area") or technical.get("legal_area"),
        action_type=case.get("action_type") or technical.get("action_type"),
        title=case.get("title") or technical.get("title"),
        description=case.get("description") or technical.get("summary"),
        default="civel",
    )
    final_status = str(decision.get("final_status") or "").strip()

    disclaimer = (
        "Saída estruturada a partir dos fatos informados, base normativa aplicável à área selecionada "
        "e critérios de viabilidade/prova. Recomendável validação profissional final antes do protocolo."
    )
    if legal_area == "familia":
        disclaimer = (
            "Saída de família estruturada para apoio jurídico supervisionado, com cuidado especial "
            "a dados sensíveis, menores, vínculo familiar e necessidade de revisão profissional antes de qualquer uso externo."
        )
    elif legal_area == "previdenciario":
        disclaimer = (
            "Saída previdenciária/assistencial estruturada para apoio jurídico supervisionado. "
            "Exige conferência de documentos administrativos, médicos, sociais, econômicos e revisão do advogado responsável."
        )
    elif legal_area in {"criminal", "penal"}:
        disclaimer = (
            "Saída criminal estruturada exclusivamente para apoio jurídico supervisionado. "
            "Não substitui análise de advogado habilitado, não representa promessa de resultado, "
            "não autoriza uso externo sem revisão profissional e não deve orientar qualquer conduta ilegal."
        )

    return {
        "normative_basis": _base_normativa_for_area(str(legal_area or "")),
        "factual_elements_considered": _elementos_faticos(case, technical),
        "probative_gaps": _lacunas_probatorias(technical),
        "analysis_context": {
            "legal_area": legal_area,
            "final_status": final_status,
            "viability_label": viability.get("label"),
            "assessment_mode": "qualitative",
        },
        "disclaimer": disclaimer,
    }
