from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.api.v1.routes.cases import _build_case_operational_context
from app.models import Case
from app.services.llm_client import LLMClientError, request_structured_analysis


DESTINATION_LABELS = {
    "linha_do_tempo": "Linha do tempo",
    "checklist": "Checklist de provas",
    "anexos": "Anexos/provas",
    "testemunhas": "Testemunhas/depoentes",
    "dossie": "Dossiê interno",
    "analise": "Análise do caso",
    "editor_minuta": "Editor/minuta",
    "contato_cliente": "Cliente/WhatsApp",
}


def _clean_text(value: Any, limit: int = 1200) -> str:
    text = str(value or "").strip()
    text = " ".join(text.split())
    return text[:limit]


def _as_list(value: Any, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _clean_text(item, limit=500)
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _load_timeline_items(db: Session, case: Case, current_user) -> list[dict[str, Any]]:
    try:
        from app.models.case_timeline import CaseTimelineItem
    except Exception:
        return []

    try:
        rows = (
            db.query(CaseTimelineItem)
            .filter(
                CaseTimelineItem.tenant_id == current_user["tenant_id"],
                CaseTimelineItem.case_id == case.id,
            )
            .order_by(
                CaseTimelineItem.sort_order.asc(),
                CaseTimelineItem.created_at.asc(),
                CaseTimelineItem.id.asc(),
            )
            .limit(20)
            .all()
        )
    except Exception:
        return []

    return [
        {
            "event_date": _clean_text(getattr(row, "event_date", ""), 120),
            "title": _clean_text(getattr(row, "title", ""), 240),
            "description": _clean_text(getattr(row, "description", ""), 500),
            "related_evidence": _clean_text(getattr(row, "related_evidence", ""), 240),
            "related_witness": _clean_text(getattr(row, "related_witness", ""), 240),
            "pending_note": _clean_text(getattr(row, "pending_note", ""), 300),
            "sort_order": getattr(row, "sort_order", 0),
        }
        for row in rows
    ]


def _clean_multiline_text(value: Any, limit: int = 6000) -> str:
    raw = str(value or "").replace("\\n", "\n").strip()
    lines = [" ".join(line.split()) for line in raw.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text[:limit]


def _suggestion(destination: str, label: str, suggested_text: str, reason: str, priority: str = "normal") -> dict[str, str]:
    return {
        "destination": destination,
        "label": label,
        "suggested_text": _clean_multiline_text(suggested_text, 6000),
        "reason": _clean_text(reason, 500),
        "priority": priority,
    }



def _case_context_text(case: Case, context: dict[str, Any]) -> str:
    parts = [
        getattr(case, "case_number", ""),
        getattr(case, "title", ""),
        getattr(case, "description", ""),
        getattr(case, "legal_area", ""),
        getattr(case, "action_type", ""),
        context.get("summary", ""),
    ]
    return _clean_text(" ".join(str(part or "") for part in parts), 3000).lower()


def _requested_guidance_modules(lowered: str) -> list[str]:
    guidance_markers = (
        "o que escrevo",
        "o que eu escrevo",
        "o que coloco",
        "o que eu coloco",
        "como preencher",
        "como monto",
        "como montar",
        "me ajude a montar",
        "me ajuda a montar",
        "o que devo preencher",
        "o que vai",
        "quais campos",
        "como faço",
        "monte",
        "monta",
        "organize",
        "organizar",
        "gere",
        "gerar",
        "crie",
        "criar",
        "liste",
        "listar",
        "fatos prontos",
        "fatos obrigatórios",
        "fatos obrigatorios",
    )

    if not any(marker in lowered for marker in guidance_markers):
        return []

    modules: list[str] = []

    if "linha do tempo" in lowered or "timeline" in lowered:
        modules.append("linha_do_tempo")

    if "checklist" in lowered or "pendência" in lowered or "pendencia" in lowered:
        modules.append("checklist")

    if "anexo" in lowered or "anexar" in lowered or "prova" in lowered or "documento" in lowered:
        modules.append("anexos")

    if "testemunha" in lowered or "depoente" in lowered or "pessoa" in lowered:
        modules.append("testemunhas")

    if "dossiê" in lowered or "dossie" in lowered:
        modules.append("dossie")

    ordered = []
    for module in modules:
        if module not in ordered:
            ordered.append(module)
    return ordered


def _is_vehicle_dealer_pix_context(blob: str) -> bool:
    lowered = blob.lower()
    has_vehicle = any(
        marker in lowered
        for marker in (
            "veículo",
            "veiculo",
            "carro",
            "automóvel",
            "automovel",
            "moto",
            "placa",
            "renavam",
            "chassi",
        )
    )
    has_dealer = any(
        marker in lowered
        for marker in (
            "revendedora",
            "garagem",
            "automóveis",
            "automoveis",
            "quintino",
            "comércio de automóveis",
            "comercio de automoveis",
        )
    )
    has_payment = any(
        marker in lowered
        for marker in (
            "pix",
            "parcela",
            "parcelas",
            "parcelamento",
            "nota promissória",
            "nota promissoria",
            "entrada",
            "r$",
        )
    )
    has_retention = any(
        marker in lowered
        for marker in (
            "bloqueio",
            "tomou",
            "recolheu",
            "retomou",
            "retomada",
            "recolhimento",
            "busca e apreensão",
            "busca e apreensao",
        )
    )
    return has_vehicle and has_dealer and (has_payment or has_retention)


def _timeline_guide_text(case: Case, context: dict[str, Any], message: str = "") -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    blob = f"{_case_context_text(case, context)} {message}".lower()

    if _is_vehicle_dealer_pix_context(blob):
        facts = [
            (
                "A confirmar",
                "Compra do veículo junto à revendedora",
                "Cliente relata que adquiriu veículo junto à revendedora, mediante negociação parcelada, com entrega de bens como entrada e pagamentos posteriores via Pix.",
                "contrato, nota promissória, mensagens com a revendedora, comprovantes de negociação e documentos do veículo adquirido",
                "cliente comprador; pessoa que acompanhou a negociação; representante da revendedora",
                "confirmar data da compra, dados do veículo adquirido, placa, Renavam, chassi, valor total contratado e condições da negociação",
            ),
            (
                "A confirmar",
                "Entrega do veículo Scenic 2004 como parte da entrada",
                "Cliente informa que entregou um veículo Scenic 2004 avaliado em R$ 4.000,00 como parte da entrada na negociação.",
                "documentos do Scenic 2004, recibo, mensagens, comprovante de transferência, avaliação ou declaração de recebimento",
                "cliente comprador; pessoa que presenciou a entrega; representante da revendedora que recebeu o bem",
                "confirmar se houve recibo, transferência, avaliação formal e identificação de quem recebeu o veículo",
            ),
            (
                "A confirmar",
                "Entrega da moto Honda CBX 300 como parte da entrada",
                "Cliente informa que entregou uma moto Honda CBX 300 avaliada em R$ 11.000,00 como parte da entrada na negociação.",
                "documentos da Honda CBX 300, recibo, mensagens, comprovante de transferência, avaliação ou declaração de recebimento",
                "cliente comprador; pessoa que presenciou a entrega; representante da revendedora que recebeu o bem",
                "confirmar se houve recibo, transferência, avaliação formal e identificação de quem recebeu a moto",
            ),
            (
                "A confirmar",
                "Pagamento de 34 parcelas via Pix",
                "Cliente informa que pagou 34 parcelas de R$ 1.180,00 via Pix, totalizando R$ 40.120,00 em parcelas pagas à revendedora ou a destinatário vinculado à negociação.",
                "comprovantes Pix, extratos bancários, identificação do destinatário dos Pix, mensagens de cobrança ou confirmação de pagamento",
                "cliente comprador; pessoa que auxiliou nos pagamentos; responsável da revendedora que recebia ou confirmava os pagamentos",
                "conferir datas, destinatários, chaves Pix, valores, soma total e eventual saldo alegado pela revendedora",
            ),
            (
                "A confirmar",
                "Perda da via física do contrato pelo comprador",
                "Cliente informa que perdeu sua via física do contrato, permanecendo pendente a obtenção de cópia junto à revendedora.",
                "relato do cliente, mensagens solicitando cópia do contrato, eventual negativa ou ausência de resposta",
                "cliente comprador; representante da revendedora responsável pelo contrato",
                "solicitar cópia integral do contrato, notas promissórias, recibos e prestação de contas",
            ),
            (
                "A confirmar",
                "Retomada ou recolhimento do veículo pela revendedora",
                "Cliente relata que a revendedora tomou ou recolheu o veículo sob alegação de suposto bloqueio, sem documentação completa apresentada até o momento.",
                "mensagens, fotos, vídeos, comprovante de guincho, localização do veículo, comunicação da revendedora ou testemunhas",
                "cliente comprador; pessoa que presenciou o recolhimento; representante da revendedora; eventual guincheiro ou terceiro",
                "confirmar data, local, quem realizou o recolhimento, onde está o veículo e qual justificativa formal foi apresentada",
            ),
            (
                "A confirmar",
                "Ausência de documentação clara sobre o suposto bloqueio",
                "Até o momento, o cliente informa não ter recebido ordem judicial, busca e apreensão, contrato, prestação de contas, documento formal da dívida ou comprovação do suposto bloqueio.",
                "mensagens de solicitação, resposta ou silêncio da revendedora, consulta Detran, consulta processual, documentos recebidos ou ausência deles",
                "cliente comprador; advogado responsável pela conferência; representante da revendedora",
                "validar documentalmente se existe bloqueio administrativo, ordem judicial, busca e apreensão ou apenas alegação comercial",
            ),
            (
                "A confirmar",
                "Avaliação jurídica das medidas cabíveis",
                "Diante da compra, entradas com bens, pagamentos via Pix e retomada/recolhimento do veículo, o caso depende de avaliação do advogado sobre exibição de contrato/documentos, restituição do veículo ou valores, danos materiais/morais e eventual tutela de urgência.",
                "conjunto documental do caso, comprovantes Pix, documentos dos bens de entrada, mensagens e consultas oficiais",
                "cliente comprador; advogado responsável; eventuais testemunhas dos fatos principais",
                "não afirmar crime, culpa ou ilegalidade definitiva sem prova; manter linguagem prudente e pendente de validação documental",
            ),
        ]
    elif "pátio" in blob or "patio" in blob or "carreta" in blob:
        facts = [
            ("A confirmar", "Entrada ou permanência da carreta no pátio", "Registrar quando, onde, por quem e por qual motivo a carreta ficou sob guarda do pátio.", "contrato, recibo, mensagens, comprovante de entrada ou documentos do pátio", "quem entregou, recebeu, autorizou ou acompanhou a guarda", "confirmar data exata, responsável pela guarda e documento de entrada"),
            ("A confirmar", "Desaparecimento, furto ou não localização da carreta", "Registrar quando foi percebido que a carreta não estava mais disponível, quem comunicou o fato e qual foi a resposta do pátio.", "BO, mensagens, ligações, fotos, comunicações e registros do pátio", "pessoa que constatou ou comunicou o desaparecimento", "confirmar data, horário, local e versão do pátio"),
            ("A confirmar", "Boletim de ocorrência e comunicações do fato", "Registrar a data do BO e demais comunicações feitas ao pátio, seguradora, locador, locatário ou responsáveis.", "boletim de ocorrência, protocolos, mensagens e e-mails", "quem registrou o BO ou participou da comunicação", "anexar BO e identificar todos os protocolos"),
            ("28/05 ou data a confirmar", "Audiência/acordo anterior envolvendo a carreta", "Registrar que houve audiência ou acordo anterior relacionado ao pagamento da carreta, sem confundir esse acordo com a responsabilidade do pátio.", "ata de audiência, termo de acordo, processo anterior", "partes presentes na audiência", "confirmar número do processo, termos do acordo e valores"),
            ("A confirmar", "Avaliação de responsabilidade do pátio", "Registrar as providências para apurar se o pátio tinha dever de guarda e se houve falha na custódia do bem.", "contrato, recibos, regulamento do pátio, mensagens, BO e documentos do veículo", "responsável do pátio, cliente, condutor ou testemunhas", "confirmar fundamento da guarda e documentos faltantes"),
        ]
    else:
        facts = [
            ("A confirmar", "Início da relação ou situação jurídica", "Registrar quando e como começou a relação entre as partes, serviço, contrato, trabalho, benefício, atendimento, guarda, compra ou conflito.", "contrato, mensagens, recibos, cadastro, protocolo ou documento inicial", "quem participou ou presenciou o início dos fatos", "confirmar data inicial e partes envolvidas"),
            ("A confirmar", "Fato principal que gerou o problema", "Registrar o acontecimento central do caso: negativa, dano, cobrança, descumprimento, acidente, dispensa, falha, perda, furto ou outro evento relevante.", "documentos, prints, fotos, vídeos, laudos, BO ou comprovantes", "quem viu, sabe ou confirma o fato", "confirmar data, local e consequências"),
            ("A confirmar", "Providências tomadas pelo cliente", "Registrar reclamações, contatos, protocolos, BO, notificações, pedidos administrativos, atendimentos ou tentativas de solução.", "protocolos, mensagens, e-mails, notificações e comprovantes", "quem recebeu ou respondeu", "organizar documentos e respostas"),
            ("A confirmar", "Situação atual e prejuízos", "Registrar o estado atual do problema, valores envolvidos, impactos, documentos faltantes e urgências.", "comprovantes de prejuízo, orçamento, laudo, extrato, recibos ou documentos atuais", "pessoas que podem confirmar o prejuízo", "quantificar valores e lacunas probatórias"),
        ]

    blocks = [f"Para o caso: {case_title}", "Preencha a Linha do Tempo por fatos, um item por vez:"]
    for index, (date, title, description, evidence, witness, pending) in enumerate(facts, start=1):
        blocks.append(
            f"\nFato {index}\n"
            f"Data/período: {date}\n"
            f"Título do fato: {title}\n"
            f"Descrição do fato: {description}\n"
            f"Prova relacionada: {evidence}\n"
            f"Testemunha/depoente relacionado: {witness}\n"
            f"Pendência/observação: {pending}\n"
            f"Ordem: {index}"
        )
    return "\n".join(blocks)

def _checklist_guide_text(case: Case, context: dict[str, Any], message: str = "") -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    blob = f"{_case_context_text(case, context)} {message}".lower()

    if _is_vehicle_dealer_pix_context(blob):
        pending_items = [
            (
                "Conferir e anexar comprovantes Pix das parcelas pagas",
                "prova",
                "alta",
                "cliente",
                "a definir",
                "Cliente informa possuir comprovantes Pix de 34 parcelas de R$ 1.180,00, totalizando R$ 40.120,00. Conferir todos os comprovantes, datas, valores, destinatário, chave Pix, banco de origem e vínculo com a negociação do veículo. Depois de conferidos, anexar os arquivos em Anexos/provas e registrar se há parcela faltante ou divergente.",
            ),
            (
                "Montar resumo cronológico dos pagamentos realizados",
                "informação",
                "alta",
                "cliente/advogado",
                "a definir",
                "Organizar os pagamentos em ordem cronológica, com data, valor, destinatário, chave Pix, banco, comprovante correspondente e observação. Confirmar se o total pago em parcelas é R$ 40.120,00 e se todos os Pix foram enviados à revendedora, representante ou pessoa vinculada à negociação.",
            ),
            (
                "Solicitar contrato, notas promissórias e prestação de contas da revendedora",
                "documento",
                "alta",
                "revendedora/cliente/advogado",
                "a definir",
                "Cliente informa que perdeu sua via física do contrato. Solicitar cópia integral do contrato, notas promissórias, recibos, demonstrativo de parcelas, saldo alegado, prestação de contas e qualquer documento usado pela revendedora para justificar a retomada ou recolhimento do veículo.",
            ),
            (
                "Comprovar bens entregues como entrada",
                "prova",
                "alta",
                "cliente",
                "a definir",
                "Levantar documentos, recibos, prints, mensagens ou comprovantes da entrega do Scenic 2004 avaliado em R$ 4.000,00 e da moto Honda CBX 300 avaliada em R$ 11.000,00. Confirmar quem recebeu os bens, data da entrega, avaliação usada e se houve transferência ou recibo.",
            ),
            (
                "Comprovar retomada ou recolhimento do veículo",
                "prova",
                "alta",
                "cliente/testemunha",
                "a definir",
                "Levantar data, local, quem recolheu, onde o veículo está, mensagens, fotos, vídeos, comprovante de guincho, comunicação da revendedora ou testemunhas que confirmem a retomada/recolhimento do veículo.",
            ),
            (
                "Verificar existência do suposto bloqueio",
                "documento",
                "alta",
                "advogado/revendedora",
                "a definir",
                "Conferir se existe ordem judicial, busca e apreensão, bloqueio administrativo, restrição Detran, documento formal de dívida ou apenas alegação comercial da revendedora. Solicitar documento formal que comprove o motivo informado.",
            ),
            (
                "Consultar Detran e eventuais processos relacionados ao veículo",
                "documento",
                "normal",
                "advogado",
                "a definir",
                "Realizar consulta de restrições administrativas/judiciais do veículo, histórico de propriedade, eventuais processos, busca e apreensão ou bloqueios vinculados. Guardar comprovantes das consultas para conferência.",
            ),
            (
                "Separar pontos para avaliação de restituição, danos e tutela",
                "informação",
                "normal",
                "advogado",
                "a definir",
                "Após reunir Pix, documentos da entrada, contrato/prestação de contas e prova do recolhimento, avaliar pedidos possíveis: exibição de documentos, restituição do veículo ou valores, danos materiais/morais e tutela de urgência. Não afirmar culpa ou ilegalidade definitiva sem prova documental.",
            ),
        ]
    else:
        pending_items = [
            (
                "Localizar documento principal do caso",
                "documento",
                "alta",
                "cliente",
                "a definir",
                "Pedir contrato, recibo, BO, mensagens, protocolos ou documento que comprove a origem do caso.",
            ),
            (
                "Confirmar datas principais",
                "informação",
                "alta",
                "cliente/testemunha",
                "a definir",
                "Confirmar data inicial, data do fato principal, comunicações feitas e situação atual.",
            ),
            (
                "Separar provas de responsabilidade e prejuízo",
                "prova",
                "alta",
                "cliente/advogado",
                "a definir",
                "Organizar documentos que mostram quem tinha obrigação, o que aconteceu, qual dano houve e o valor envolvido.",
            ),
        ]

    blocks = [f"Para o caso: {case_title}", "No Checklist de provas, crie pendências objetivas:"]
    for index, (title, category, priority, requested_from, deadline, notes) in enumerate(pending_items, start=1):
        blocks.append(
            f"\nPendência {index}\n"
            f"Título: {title}\n"
            f"Categoria: {category}\n"
            f"Prioridade: {priority}\n"
            f"Solicitar de: {requested_from}\n"
            f"Prazo: {deadline}\n"
            f"Observações: {notes}"
        )
    return "\n".join(blocks)

def _attachments_guide_text(case: Case, context: dict[str, Any], message: str = "") -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    blob = f"{_case_context_text(case, context)} {message}".lower()

    if _is_vehicle_dealer_pix_context(blob):
        has_license = any(
            marker in blob
            for marker in (
                "licenciamento",
                "licenciamentos",
                "ipva",
                "documento anual",
                "taxa do veículo",
                "taxa do veiculo",
            )
        )

        available = [
            (
                "Comprovantes Pix das parcelas pagas",
                "comprovante de pagamento",
                "Comprovante Pix de parcela do veículo adquirido junto à revendedora. Usar para conferência de data, valor, destinatário, chave Pix, banco de origem e vínculo com a negociação.",
                "Ajuda a demonstrar pagamento de parcelas, histórico de adimplemento informado pelo cliente e valor econômico já desembolsado.",
                "Conferir se todos os comprovantes correspondem à negociação, se o destinatário é a revendedora/representante e se o total bate com as 34 parcelas de R$ 1.180,00.",
            ),
        ]

        if has_license:
            available.append(
                (
                    "Comprovantes de pagamento dos licenciamentos",
                    "comprovante de despesa vinculada ao veículo",
                    "Comprovante de pagamento de licenciamento/IPVA/taxa do veículo relacionado ao caso. Usar para demonstrar despesa assumida pelo cliente e vínculo com a posse/uso do veículo.",
                    "Ajuda a demonstrar gastos feitos pelo cliente com o veículo, além das parcelas, e pode compor análise de prejuízos materiais.",
                    "Confirmar ano, placa/veículo, CPF/CNPJ pagador, valor, data e se o pagamento se refere ao veículo objeto do caso.",
                )
            )

        pending = [
            "Contrato de compra e venda ou financiamento/parcelamento firmado com a revendedora.",
            "Notas promissórias, recibos, carnês, demonstrativo de parcelas ou confissão de dívida.",
            "Recibos ou documentos da entrada com Scenic 2004 e Honda CBX 300.",
            "Prestação de contas da revendedora com valores pagos, saldo alegado e motivo da retomada/recolhimento.",
            "Documento formal do suposto bloqueio, ordem judicial, busca e apreensão, restrição Detran ou justificativa administrativa.",
            "Prova da retomada/recolhimento: mensagens, fotos, vídeos, guincho, local onde o veículo está ou testemunhas.",
            "Consultas Detran e eventuais consultas processuais vinculadas ao veículo ou às partes.",
        ]

        risks = [
            "Sem contrato, fica pendente confirmar valor total, cláusulas, vencimentos, multa, saldo e autorização contratual alegada.",
            "Sem documento do suposto bloqueio, não se deve afirmar irregularidade definitiva; é necessário validar se houve ordem judicial, restrição administrativa ou mera alegação comercial.",
            "Sem prestação de contas, o cálculo de saldo, devolução, restituição ou indenização fica pendente de conferência.",
            "Sem prova da retomada/recolhimento, é importante buscar mensagens, testemunhas ou documento que confirme data, local, responsável e destino do veículo.",
        ]

        blocks = [
            f"Para o caso: {case_title}",
            "Em Anexos/provas, anexe apenas arquivos reais. Não trate relato digitado como prova sem documento correspondente.",
            "",
            "Provas disponíveis para anexar agora:",
        ]

        for index, (title, kind, description, proves, caution) in enumerate(available, start=1):
            blocks.append(
                f"\nAnexo disponível {index}\n"
                f"Tipo: {kind}\n"
                f"Nome/descrição sugerida: {title}\n"
                f"Descrição para o anexo: {description}\n"
                f"O que comprova: {proves}\n"
                f"Cuidado/conferência: {caution}"
            )

        blocks.append("\nProvas/documentos ainda pendentes:")
        for index, item in enumerate(pending, start=1):
            blocks.append(f"{index}. {item}")

        blocks.append("\nRiscos por falta de documentos:")
        for index, item in enumerate(risks, start=1):
            blocks.append(f"{index}. {item}")

        blocks.append(
            "\nPróximas providências:\n"
            "1. Anexar primeiro os comprovantes Pix e, se existirem, os comprovantes de licenciamentos.\n"
            "2. Descrever cada arquivo de forma objetiva, sem aumentar o conteúdo do documento.\n"
            "3. Criar pendências no Checklist para contrato, prestação de contas, entrada com bens, suposto bloqueio e prova do recolhimento.\n"
            "4. Depois de anexar as provas reais, atualizar o Dossiê interno para consolidar o que já existe e o que ainda falta."
        )

        return "\n".join(blocks)

    return f"""Para o caso: {case_title}
Em Anexos/provas, só envie documentos reais. Para cada arquivo, descreva o que ele comprova.

Anexo sugerido 1
Tipo: documento principal
Descrição: comprova a relação entre as partes ou a origem da obrigação.

Anexo sugerido 2
Tipo: comunicação/protocolo
Descrição: comprova que o fato foi comunicado ou que houve tentativa de solução.

Anexo sugerido 3
Tipo: prova do dano/prejuízo
Descrição: comprova valor, perda, dano, pagamento, orçamento, laudo ou consequência do fato.

Cuidado: texto digitado não substitui prova. Quando citar BO, contrato, print, foto ou mensagem, tente anexar o arquivo correspondente."""



def _witness_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    return f"""Para o caso: {case_title}
Em Testemunhas/depoentes, cadastre pessoas que possam confirmar fatos, datas, guarda, comunicação, dano ou providências.

Pessoa 1
Nome: a confirmar
Papel: cliente/parte envolvida
O que sabe ou confirma: explica a narrativa principal, documentos disponíveis, datas e prejuízos.

Pessoa 2
Nome: a confirmar
Papel: testemunha/depoente
O que sabe ou confirma: viu, recebeu, entregou, comunicou, acompanhou ou pode confirmar algum fato da linha do tempo.

Pessoa 3
Nome: a confirmar
Papel: representante/responsável da outra parte ou terceiro
O que sabe ou confirma: pode esclarecer responsabilidade, guarda, resposta dada, protocolos ou documentos emitidos.

Cuidado: não inventar testemunha. Se o nome ainda não existir, cadastre como pendência no Checklist."""


def _dossier_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    return f"""Para o caso: {case_title}
O Dossiê interno deve ser atualizado depois de preencher os módulos principais.

Antes de atualizar o dossiê, confira:
1. Linha do Tempo com os fatos principais.
2. Checklist com documentos e pendências.
3. Anexos/provas reais já enviados.
4. Testemunhas/depoentes ou pessoas-chave.
5. Dados do cliente e WhatsApp, se aplicável.

Depois clique em Atualizar dossiê. Ele serve para visão operacional do advogado, não é peça processual e não substitui revisão jurídica."""


def _module_guide_suggestion(destination: str, case: Case, context: dict[str, Any], message: str = "") -> dict[str, str]:
    if destination == "linha_do_tempo":
        return _suggestion(
            "linha_do_tempo",
            "Preencher Linha do Tempo por campos",
            _timeline_guide_text(case, context, message),
            "A pergunta é sobre como preencher a Linha do Tempo; a resposta deve orientar campo por campo, não tratar a pergunta como fato.",
            "alta",
        )

    if destination == "checklist":
        return _suggestion(
            "checklist",
            "Preencher Checklist de provas",
            _checklist_guide_text(case, context, message),
            "A pergunta pede organização de pendências e documentos; isso pertence ao Checklist.",
            "alta",
        )

    if destination == "anexos":
        return _suggestion(
            "anexos",
            "Organizar Anexos/provas",
            _attachments_guide_text(case, context, message),
            "A pergunta envolve documentos/provas que devem ser anexados quando existirem arquivos reais.",
            "normal",
        )

    if destination == "testemunhas":
        return _suggestion(
            "testemunhas",
            "Preencher Testemunhas/depoentes",
            _witness_guide_text(case, context),
            "A pergunta envolve pessoas que podem confirmar fatos e devem ser cadastradas com papel e o que sabem.",
            "normal",
        )

    return _suggestion(
        "dossie",
        "Atualizar Dossiê interno",
        _dossier_guide_text(case, context),
        "O dossiê consolida o que foi preenchido nos módulos do caso.",
        "normal",
    )


def _module_guidance_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
    modules: list[str],
) -> dict[str, Any]:
    suggestions = [_module_guide_suggestion(module, case, context, message) for module in modules]

    if "dossie" not in modules:
        suggestions.append(_module_guide_suggestion("dossie", case, context, message))

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": "Entendi que você quer orientação de preenchimento. Vou responder por campos, para copiar e adaptar dentro do módulo correto.",
        "rewritten_input": _clean_text(message, 2500),
        "suggested_actions": suggestions[:8],
        "next_steps": [
            "Clique no botão Abrir do módulo indicado.",
            "Copie/adapte os campos sugeridos.",
            "Salve um item por vez, revisando datas, documentos e nomes.",
            "Depois atualize o Dossiê interno para consolidar a visão do caso.",
        ],
        "warnings": [
            "Esta V1 orienta o preenchimento, mas não salva dados automaticamente.",
            "Não invente datas, documentos, valores ou testemunhas. Use 'a confirmar' quando faltar informação.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_module_guidance_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "requested_modules": modules,
            "timeline_items_considered": len(timeline),
        },
    }


def _fallback_response(case: Case, message: str, context: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    text = _clean_text(message, 2500)
    lowered = text.lower()

    requested_guidance_modules = _requested_guidance_modules(lowered)
    if requested_guidance_modules:
        return _module_guidance_response(
            case=case,
            message=text,
            context=context,
            timeline=timeline,
            modules=requested_guidance_modules,
        )

    suggestions: list[dict[str, str]] = []

    has_fact = any(
        marker in lowered
        for marker in (
            "aconteceu",
            "ocorreu",
            "fato",
            "evento",
            "data",
            "dia ",
            "quando",
            "antes",
            "depois",
            "pagou",
            "pagamento",
            "audiência",
            "audiencia",
            "contratou",
            "demitiu",
            "dispensou",
            "comprou",
            "vendeu",
            "negou",
            "recusou",
            "sumiu",
            "furto",
            "roubo",
            "ameaça",
            "ameaca",
            "agressão",
            "agressao",
            "acidente",
            "doença",
            "doenca",
            "benefício",
            "beneficio",
            "inss",
            "cliente informou",
            "cliente disse",
        )
    )
    has_document = any(
        marker in lowered
        for marker in (
            "bo",
            "boletim",
            "contrato",
            "comprovante",
            "nota fiscal",
            "print",
            "foto",
            "imagem",
            "áudio",
            "audio",
            "vídeo",
            "video",
            "documento",
            "seguro",
            "laudo",
            "atestado",
            "receita",
            "exame",
            "holerite",
            "contracheque",
            "ctps",
            "rescisão",
            "rescisao",
            "termo",
            "declaração",
            "declaracao",
            "sentença",
            "sentenca",
            "decisão",
            "decisao",
            "notificação",
            "notificacao",
            "mensagem",
            "whatsapp",
            "email",
            "e-mail",
        )
    )
    has_person = any(
        marker in lowered
        for marker in (
            "testemunha",
            "depoente",
            "viu",
            "presenciou",
            "confirmou",
            "sabe",
            "relatou",
            "declarou",
            "cliente falou",
            "cliente disse",
            "pessoa",
            "parte",
            "autor",
            "réu",
            "reu",
            "empregado",
            "empregador",
            "consumidor",
            "fornecedor",
            "médico",
            "medico",
            "perito",
            "servidor",
            "fiscal",
            "motorista",
            "condutor",
        )
    )

    if has_fact or not suggestions:
        suggestions.append(
            _suggestion(
                "linha_do_tempo",
                "Organizar como fato do caso",
                text,
                "A informação parece narrar um acontecimento relevante e deve ser organizada em ordem cronológica.",
                "alta" if has_fact else "normal",
            )
        )

    if has_document:
        suggestions.append(
            _suggestion(
                "checklist",
                "Criar ou revisar pendência probatória",
                "Conferir/anexar documento mencionado: contrato, comprovante, print, foto, áudio, vídeo, laudo, BO, decisão, notificação, mensagem ou outro registro citado.",
                "Documentos citados precisam entrar no checklist de pendências/provas e, quando existirem, também nos anexos/provas.",
                "alta",
            )
        )
        suggestions.append(
            _suggestion(
                "anexos",
                "Anexar prova documental",
                "Anexar o documento citado e descrever de forma objetiva o que ele comprova.",
                "O sistema não deve tratar uma informação digitada como prova sem o respectivo arquivo/documento.",
                "normal",
            )
        )

    if has_person:
        suggestions.append(
            _suggestion(
                "testemunhas",
                "Cadastrar pessoa-chave",
                "Cadastrar nome, papel e o que a pessoa sabe ou confirma sobre o fato.",
                "A informação parece envolver pessoa relevante, testemunha, depoente, parte ou alguém que pode confirmar fatos.",
                "alta",
            )
        )

    suggestions.append(
        _suggestion(
            "dossie",
            "Atualizar visão operacional",
            "Depois de organizar a informação nos módulos corretos, atualizar o dossiê interno do caso.",
            "O dossiê consolida timeline, checklist, anexos, testemunhas e prontidão para apoiar a decisão do advogado.",
            "normal",
        )
    )

    context_summary = _clean_text(context.get("summary"), 700)
    timeline_count = len(timeline)

    next_steps = [
        "Revisar a sugestão antes de copiar para qualquer campo.",
        "Salvar o fato na Linha do Tempo se ele representar um acontecimento do caso.",
        "Criar pendência no Checklist se depender de documento, prova ou confirmação.",
        "Atualizar o Dossiê depois de cadastrar as informações nos módulos corretos.",
    ]

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": (
            "Entendi a informação e organizei em orientação operacional para o caso. "
            "Nenhum dado foi salvo automaticamente."
        ),
        "rewritten_input": text,
        "suggested_actions": suggestions[:6],
        "next_steps": next_steps,
        "warnings": [
            "Esta V1 apenas orienta; ela não salva timeline, checklist, anexos, testemunhas ou minuta automaticamente.",
            "Toda sugestão deve ser revisada por advogado responsável antes de uso jurídico.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "context_summary": context_summary,
            "timeline_items_considered": timeline_count,
        },
    }


def _normalize_suggestions(value: Any, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    raw_items = value if isinstance(value, list) else []
    items: list[dict[str, str]] = []

    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        destination = _clean_text(raw.get("destination"), 80) or "linha_do_tempo"
        if destination not in DESTINATION_LABELS:
            destination = "linha_do_tempo"

        items.append(
            _suggestion(
                destination=destination,
                label=_clean_text(raw.get("label"), 160) or DESTINATION_LABELS[destination],
                suggested_text=_clean_text(raw.get("suggested_text"), 900),
                reason=_clean_text(raw.get("reason"), 500) or "Sugestão operacional gerada a partir da mensagem e do contexto do caso.",
                priority=_clean_text(raw.get("priority"), 40) or "normal",
            )
        )

        if len(items) >= 8:
            break

    return items or fallback


def _normalize_response(raw: dict[str, Any], fallback: dict[str, Any], case_id: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return fallback

    suggestions = _normalize_suggestions(
        raw.get("suggested_actions") or raw.get("actions") or raw.get("suggestions"),
        fallback.get("suggested_actions", []),
    )

    warnings = _as_list(raw.get("warnings"), limit=5) or fallback["warnings"]
    if not any("não salva" in warning.lower() or "não salva" in warning.lower() for warning in warnings):
        warnings.insert(0, "Esta V1 apenas orienta; ela não salva dados automaticamente.")

    return {
        "case_id": case_id,
        "assistant_mode": "orientation_only",
        "summary": _clean_text(raw.get("summary"), 900) or fallback["summary"],
        "rewritten_input": _clean_text(raw.get("rewritten_input"), 2500) or fallback["rewritten_input"],
        "suggested_actions": suggestions,
        "next_steps": _as_list(raw.get("next_steps"), limit=8) or fallback["next_steps"],
        "warnings": warnings[:6],
        "disclaimer": _clean_text(raw.get("disclaimer"), 700) or fallback["disclaimer"],
        "metadata": {
            **dict(fallback.get("metadata") or {}),
            "provider": "llm",
            "source": "case_operational_assistant_v1",
        },
    }


def _build_prompt(case: Case, message: str, context: dict[str, Any], timeline: list[dict[str, Any]]) -> str:
    payload = {
        "case": {
            "id": getattr(case, "id", None),
            "case_number": getattr(case, "case_number", ""),
            "title": getattr(case, "title", ""),
            "description": getattr(case, "description", ""),
            "legal_area": getattr(case, "legal_area", ""),
            "action_type": getattr(case, "action_type", ""),
            "status": getattr(case, "status", ""),
        },
        "operational_context": context,
        "timeline": timeline,
        "lawyer_message": message,
    }

    return f"""
Você é uma IA assistente operacional universal de um painel jurídico multiárea.
Você atua como copiloto operacional dentro do caso aberto, independentemente da área jurídica.
Sua função é ajudar o advogado a entender, corrigir, organizar e decidir ONDE colocar cada informação dentro do sistema.

REGRAS:
- Responda apenas em JSON válido.
- Não diga que salvou dados.
- Não crie peça processual final.
- Não prometa resultado judicial.
- Seja prático, objetivo e operacional.
- Quando a mensagem for uma pergunta de orientação do tipo "o que escrevo", "o que coloco", "como preencher", "como montar" ou "me ajude a montar", NÃO trate a pergunta como fato do caso.
- Nesses casos, entregue um guia preenchível por campos do módulo solicitado, com exemplos práticos e textos que o advogado possa copiar/adaptar.
- Se o advogado pedir vários módulos na mesma mensagem, inclua uma sugestão para cada módulo solicitado.
- Quando houver fato cronológico, evento, data, sequência ou narrativa de acontecimento, sugira Linha do Tempo.
- Quando houver documento, prova, arquivo, print, áudio, vídeo, contrato, laudo, decisão, BO, notificação, comprovante ou prova faltante, sugira Checklist e/ou Anexos.
- Quando houver pessoa envolvida, parte, testemunha, depoente, servidor, médico, perito, fiscal, empregado, empregador, consumidor, fornecedor ou alguém que viu/sabe/confirma, sugira Testemunhas/depoentes ou Cliente/WhatsApp conforme o caso.
- Quando a informação ajudar a consolidar visão estratégica/operacional, sugira Dossiê.
- Quando a informação parecer fundamento, tese, risco, pedido, estratégia ou dúvida técnica, sugira Análise do caso.
- Quando a informação parecer texto aproveitável para petição, manifestação, audiência, recurso ou minuta, sugira Editor/minuta.
- Sempre mantenha revisão humana obrigatória.

DESTINOS permitidos:
linha_do_tempo, checklist, anexos, testemunhas, dossie, analise, editor_minuta, contato_cliente

JSON obrigatório:
{{
  "summary": "resumo do que entendeu",
  "rewritten_input": "versão corrigida e mais clara da informação enviada",
  "suggested_actions": [
    {{
      "destination": "linha_do_tempo",
      "label": "nome curto da ação",
      "suggested_text": "texto sugerido para copiar ou adaptar",
      "reason": "por que isso vai nesse módulo",
      "priority": "alta|normal|baixa"
    }}
  ],
  "next_steps": ["passo 1", "passo 2"],
  "warnings": ["alerta operacional"],
  "disclaimer": "aviso de revisão humana"
}}

DADOS:
{json.dumps(payload, ensure_ascii=False, default=str)}
""".strip()


def build_case_operational_assistant_response(
    db: Session,
    case: Case,
    current_user,
    message: str,
) -> dict[str, Any]:
    cleaned_message = _clean_text(message, 6000)

    context = _build_case_operational_context(db=db, case=case, current_user=current_user)
    timeline = _load_timeline_items(db=db, case=case, current_user=current_user)
    fallback = _fallback_response(case=case, message=cleaned_message, context=context, timeline=timeline)

    try:
        raw = request_structured_analysis(_build_prompt(case=case, message=cleaned_message, context=context, timeline=timeline))
    except LLMClientError:
        return fallback
    except Exception:
        return fallback

    return _normalize_response(raw=raw, fallback=fallback, case_id=case.id)
