from __future__ import annotations

import re

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




def _is_evidence_availability_message(lowered: str) -> bool:
    availability_markers = (
        "por enquanto",
        "só possui",
        "so possui",
        "só tenho",
        "so tenho",
        "só temos",
        "so temos",
        "cliente só possui",
        "cliente so possui",
        "cliente possui",
        "cliente tem",
        "possui",
        "tenho",
        "temos",
        "já possui",
        "ja possui",
        "já tenho",
        "ja tenho",
        "não possui",
        "nao possui",
        "não tenho",
        "nao tenho",
        "não temos",
        "nao temos",
        "ainda não possui",
        "ainda nao possui",
        "ainda não tenho",
        "ainda nao tenho",
        "não tem",
        "nao tem",
        "faltam",
        "falta",
        "pendente",
        "pendentes",
        "disponível",
        "disponivel",
        "disponíveis",
        "disponiveis",
        "provas disponíveis",
        "provas disponiveis",
        "documentos disponíveis",
        "documentos disponiveis",
    )
    evidence_markers = (
        "prova",
        "provas",
        "anexo",
        "anexos",
        "documento",
        "documentos",
        "contrato",
        "comprovante",
        "comprovantes",
        "recibo",
        "recibos",
        "nota fiscal",
        "print",
        "prints",
        "foto",
        "fotos",
        "imagem",
        "áudio",
        "audio",
        "vídeo",
        "video",
        "laudo",
        "atestado",
        "receita",
        "exame",
        "holerite",
        "contracheque",
        "ctps",
        "rescisão",
        "rescisao",
        "declaração",
        "declaracao",
        "bo",
        "boletim",
        "mensagem",
        "mensagens",
        "whatsapp",
        "email",
        "e-mail",
        "licenciamento",
        "licenciamentos",
        "ipva",
        "pix",
        "extrato",
        "extratos",
    )
    has_availability = any(marker in lowered for marker in availability_markers)
    has_evidence = any(marker in lowered for marker in evidence_markers)
    return has_availability and has_evidence


def _evidence_availability_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    suggestions = [
        _module_guide_suggestion("anexos", case, context, message),
        _module_guide_suggestion("checklist", case, context, message),
        _module_guide_suggestion("dossie", case, context, message),
    ]

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": "Entendi que você está informando quais provas ou documentos existem e quais ainda faltam. Vou tratar isso como organização probatória, não como fato da Linha do Tempo.",
        "rewritten_input": _clean_text(message, 2500),
        "suggested_actions": suggestions[:8],
        "next_steps": [
            "Anexar apenas arquivos reais em Anexos/provas.",
            "Criar ou revisar pendências no Checklist para documentos que ainda faltam.",
            "Não salvar essa informação como fato cronológico, salvo se houver uma data/evento concreto a registrar.",
            "Depois atualize o Dossiê interno para consolidar provas disponíveis e pendências.",
        ],
        "warnings": [
            "Texto digitado não substitui prova documental.",
            "Não invente documentos, datas, valores, testemunhas ou conteúdo de anexos.",
            "Quando um documento ainda não existir, mantenha como pendência no Checklist.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_evidence_availability_routing_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "timeline_items_considered": len(timeline),
        },
    }


def _is_natural_next_step_message(lowered: str) -> bool:
    text = f" {lowered.strip()} "
    if not text.strip():
        return False

    next_step_markers = (
        "qual próximo passo",
        "qual proximo passo",
        "próximo passo",
        "proximo passo",
        "e agora",
        "agora o que",
        "o que faço agora",
        "o que faco agora",
        "faço o quê",
        "faco o que",
        "faço o que",
        "como continuo",
        "como continuar",
        "posso continuar",
        "depois disso faço",
        "depois disso faco",
        "depois disso o que",
        "após isso faço",
        "apos isso faco",
        "após isso o que",
        "apos isso o que",
    )
    if any(marker in text for marker in next_step_markers):
        return True

    completion_markers = (
        "terminei",
        "preenchi",
        "preenchido",
        "cadastrei",
        "coloquei",
        "lancei",
        "salvei",
        "já fiz",
        "ja fiz",
        "já preenchi",
        "ja preenchi",
        "já cadastrei",
        "ja cadastrei",
        "já terminei",
        "ja terminei",
    )
    module_markers = (
        "checklist",
        "linha do tempo",
        "timeline",
        "anexo",
        "anexos",
        "prova",
        "provas",
        "testemunha",
        "testemunhas",
        "depoente",
        "depoentes",
        "dossiê",
        "dossie",
        "caso",
        "processo",
    )

    return any(marker in text for marker in completion_markers) and any(
        marker in text for marker in module_markers
    )


def _natural_next_step_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    text = _clean_text(message, 2500)
    lowered = text.lower()

    mentions_checklist = "checklist" in lowered
    mentions_timeline = "linha do tempo" in lowered or "timeline" in lowered
    mentions_attachments = any(marker in lowered for marker in ("anexo", "anexos", "prova", "provas"))
    mentions_people = any(
        marker in lowered
        for marker in ("testemunha", "testemunhas", "depoente", "depoentes")
    )

    if mentions_checklist:
        summary = (
            "Entendi que o Checklist já foi preenchido ou revisado. "
            "O próximo passo é consolidar o caso e separar o que ainda falta, sem transformar essa pergunta em fato da Linha do Tempo."
        )
    elif mentions_timeline:
        summary = (
            "Entendi que a Linha do Tempo já foi preenchida ou revisada. "
            "O próximo passo é conferir provas, pessoas envolvidas e atualizar o Dossiê interno."
        )
    elif mentions_attachments:
        summary = (
            "Entendi que você está avançando na parte de Anexos/provas. "
            "O próximo passo é conferir se os arquivos reais foram anexados e depois consolidar isso no Dossiê interno."
        )
    elif mentions_people:
        summary = (
            "Entendi que você está avançando na parte de Testemunhas/depoentes. "
            "O próximo passo é conferir se o que cada pessoa sabe está claro e depois atualizar o Dossiê interno."
        )
    else:
        summary = (
            "Entendi que você está perguntando o próximo passo operacional do caso. "
            "Vou orientar o fluxo sem tratar essa mensagem como fato cronológico."
        )

    suggestions = [
        _suggestion(
            "dossie",
            "Atualizar Dossiê interno",
            "Consolidar o que já foi preenchido, o que ainda falta e quais pontos dependem de documento, prova ou revisão.",
            "O Dossiê interno deve virar a visão executiva do caso antes de nova análise ou minuta.",
            "alta",
        ),
        _suggestion(
            "anexos",
            "Anexar provas reais quando disponíveis",
            "Quando os arquivos estiverem em mãos, anexar comprovantes, contratos, prints, documentos, fotos, áudios, vídeos ou consultas oficiais.",
            "Texto digitado ajuda a organizar, mas não substitui o arquivo/documento real.",
            "alta" if mentions_checklist or mentions_attachments else "normal",
        ),
        _suggestion(
            "testemunhas",
            "Conferir pessoas/testemunhas",
            "Cadastrar ou revisar pessoas que possam confirmar fatos, pagamentos, entrega de bens, recolhimento, conversas ou outras informações relevantes.",
            "Se não houver testemunha ou depoente por enquanto, manter como pendência operacional.",
            "normal",
        ),
        _suggestion(
            "linha_do_tempo",
            "Conferir Linha do Tempo",
            "Verificar se os principais acontecimentos do caso estão em ordem cronológica, com prova relacionada ou pendência indicada.",
            "A pergunta de próximo passo não deve ser salva como fato; apenas fatos concretos do caso entram na Linha do Tempo.",
            "normal" if mentions_timeline else "baixa",
        ),
    ]

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": summary,
        "rewritten_input": text,
        "suggested_actions": suggestions[:6],
        "next_steps": [
            "Não salvar esta pergunta como fato da Linha do Tempo.",
            "Atualizar o Dossiê interno para consolidar o que já foi feito e o que ainda falta.",
            "Manter Anexos/provas como pendência quando depender de arquivo real ainda não levantado.",
            "Conferir se Linha do Tempo, Checklist e Testemunhas/depoentes estão coerentes entre si.",
            "Depois de consolidar os módulos principais, pedir nova análise do caso.",
        ],
        "warnings": [
            "Esta orientação não salva dados automaticamente.",
            "Não invente documentos, datas, valores, testemunhas ou conteúdo de anexos.",
            "Toda informação jurídica deve ser revisada por profissional responsável antes de uso real.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_natural_next_step_routing_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "timeline_items_considered": len(timeline),
        },
    }




EDITOR_BLOCK_LABELS: tuple[tuple[str, str], ...] = (
    ("endereçamento", "Endereçamento"),
    ("enderecamento", "Endereçamento"),
    ("qualificação das partes", "Qualificação das Partes"),
    ("qualificacao das partes", "Qualificação das Partes"),
    ("resumo fático", "Resumo Fático"),
    ("resumo fatico", "Resumo Fático"),
    ("fundamentação", "Fundamentação"),
    ("fundamentacao", "Fundamentação"),
    ("pedidos e valores estimados", "Pedidos e Valores Estimados"),
    ("provas e requerimentos", "Provas e Requerimentos"),
    ("checklist final", "Checklist Final"),
    ("fechamento", "Fechamento"),
    ("pedidos", "Pedidos"),
)


def _detect_editor_block_label(lowered: str) -> str:
    explicit_headers: tuple[tuple[str, str], ...] = (
        ("pedidos e valores estimados — draft", "Pedidos e Valores Estimados"),
        ("pedidos e valores estimados - draft", "Pedidos e Valores Estimados"),
        ("provas e requerimentos — draft", "Provas e Requerimentos"),
        ("provas e requerimentos - draft", "Provas e Requerimentos"),
        ("qualificação das partes — draft", "Qualificação das Partes"),
        ("qualificacao das partes — draft", "Qualificação das Partes"),
        ("qualificação das partes - draft", "Qualificação das Partes"),
        ("qualificacao das partes - draft", "Qualificação das Partes"),
        ("resumo fático — draft", "Resumo Fático"),
        ("resumo fatico — draft", "Resumo Fático"),
        ("resumo fático - draft", "Resumo Fático"),
        ("resumo fatico - draft", "Resumo Fático"),
        ("fundamentação — draft", "Fundamentação"),
        ("fundamentacao — draft", "Fundamentação"),
        ("fundamentação - draft", "Fundamentação"),
        ("fundamentacao - draft", "Fundamentação"),
        ("endereçamento — draft", "Endereçamento"),
        ("enderecamento — draft", "Endereçamento"),
        ("endereçamento - draft", "Endereçamento"),
        ("enderecamento - draft", "Endereçamento"),
        ("checklist final — draft", "Checklist Final"),
        ("checklist final - draft", "Checklist Final"),
        ("fechamento — draft", "Fechamento"),
        ("fechamento - draft", "Fechamento"),
        ("pedidos — draft", "Pedidos"),
        ("pedidos - draft", "Pedidos"),
    )

    for marker, label in explicit_headers:
        if marker in lowered:
            return label

    for marker, label in EDITOR_BLOCK_LABELS:
        if marker in lowered:
            return label

    return "Bloco editável"



def _is_editor_block_pure_text_message(lowered: str) -> bool:
    text = f" {lowered.strip()} "
    if not text.strip():
        return False

    block_intent_markers = (
        "reescreva somente o bloco",
        "reescrever somente o bloco",
        "somente o bloco",
        "texto final pronto",
        "pronto para copiar e colar",
        "comece direto pelo texto do bloco",
        "entregue apenas o texto final",
        "não traga checklist",
        "nao traga checklist",
        "não traga linha do tempo",
        "nao traga linha do tempo",
        "não traga anexos",
        "nao traga anexos",
        "não traga alertas",
        "nao traga alertas",
    )

    editor_block_markers = (
        "resumo fático",
        "resumo fatico",
        "fundamentação",
        "fundamentacao",
        "pedidos",
        "endereçamento",
        "enderecamento",
        "provas e requerimentos",
        "checklist final",
        "fechamento",
        "[nome do bloco]",
    )

    return any(marker in text for marker in block_intent_markers) and any(marker in text for marker in editor_block_markers)


def _is_editor_all_blocks_ready_message(lowered: str) -> bool:
    text = f" {lowered.strip()} "
    if not text.strip():
        return False

    all_blocks_intent_markers = (
        "gere todos os blocos",
        "todos os blocos principais",
        "blocos principais da minuta",
        "todos os blocos da minuta",
        "separados por títulos exatamente assim",
        "separados por titulos exatamente assim",
        "comece direto pelo bloco 1",
    )

    required_block_markers = (
        "bloco 1",
        "bloco 2",
        "bloco 3",
        "bloco 4",
        "bloco 5",
        "bloco 6",
        "bloco 7",
        "qualificação das partes",
        "qualificacao das partes",
        "resumo fático",
        "resumo fatico",
        "fundamentação preliminar",
        "fundamentacao preliminar",
        "provas e requerimentos",
        "fechamento",
    )

    return any(marker in text for marker in all_blocks_intent_markers) and sum(
        1 for marker in required_block_markers if marker in text
    ) >= 4


def _is_editor_block_correction_message(lowered: str) -> bool:
    text = f" {lowered.strip()} "
    if not text.strip():
        return False

    block_markers = (
        "— draft",
        "- draft",
        "(assisted_draft)",
        "blocos da versão",
        "blocos da versao",
        "editar bloco",
        "versão atual",
        "versao atual",
        "resumo fático",
        "resumo fatico",
        "endereçamento",
        "enderecamento",
        "fundamentação",
        "fundamentacao",
        "pedidos",
        "provas e requerimentos",
        "checklist final",
    )
    correction_markers = (
        "corrige",
        "corrigir",
        "como está",
        "como esta",
        "ta bom",
        "tá bom",
        "t bom",
        "precisa mexer",
        "precisa mudar",
        "precisa ajustar",
        "está viável",
        "esta viavel",
        "tá viável",
        "ta viavel",
        "verifique",
        "verificar",
        "confere",
        "confira",
        "conferir",
        "conferência",
        "conferencia",
        "está de acordo",
        "esta de acordo",
        "se está de acordo",
        "se esta de acordo",
        "está correto",
        "esta correto",
        "está certo",
        "esta certo",
        "avalia",
        "avalie",
        "analisar esse bloco",
        "analise esse bloco",
        "revisa",
        "revise",
    )

    return any(marker in text for marker in block_markers) and any(
        marker in text for marker in correction_markers
    )



def _format_resumo_fatico_paragraphs(text: str) -> str:
    cleaned = " ".join(str(text or "").replace("\r\n", "\n").replace("\n", " ").split())
    if not cleaned:
        return ""

    paragraph_starters = (
        "Cliente relata",
        "O cliente relata",
        "Informa que",
        "Além da entrada",
        "Considerando a entrada",
        "O cliente informa",
        "Após os pagamentos",
        "A narrativa permanece",
    )

    for starter in paragraph_starters:
        cleaned = cleaned.replace(f" {starter}", f"\n\n{starter}")

    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")

    return cleaned.strip()



def _clean_editor_block_suggested_text(text: str, max_length: int = 6000) -> str:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    previous_blank = False

    for raw_line in raw.split("\n"):
        line = " ".join(raw_line.strip().split())

        if not line:
            if lines and not previous_blank:
                lines.append("")
            previous_blank = True
            continue

        lines.append(line)
        previous_blank = False

    cleaned = "\n".join(lines).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()

    return cleaned


def _extract_editor_block_body(message: str) -> str:
    raw_text = str(message or "").replace("\r\n", "\n").strip()
    if not raw_text:
        return ""

    lowered = raw_text.lower()
    block_markers = (
        "endereçamento — draft",
        "enderecamento — draft",
        "resumo fático — draft",
        "resumo fatico — draft",
        "fundamentação — draft",
        "fundamentacao — draft",
        "pedidos — draft",
        "provas e requerimentos — draft",
        "checklist final — draft",
        "endereçamento - draft",
        "enderecamento - draft",
        "resumo fático - draft",
        "resumo fatico - draft",
        "fundamentação - draft",
        "fundamentacao - draft",
        "pedidos - draft",
        "provas e requerimentos - draft",
        "checklist final - draft",
    )

    start_index = -1
    for marker in block_markers:
        found = lowered.find(marker)
        if found >= 0 and (start_index < 0 or found < start_index):
            start_index = found

    if start_index >= 0:
        raw_text = raw_text[start_index:]

    # O frontend pode enviar o título do bloco e o conteúdo na mesma linha.
    # Ex.: "Resumo Fático — draft (assisted_draft) Trata-se..."
    # Por isso removemos apenas o cabeçalho do bloco, preservando o corpo.
    raw_text_lowered = raw_text.lower()
    for marker in block_markers:
        if raw_text_lowered.startswith(marker):
            raw_text = raw_text[len(marker):].lstrip()
            raw_text_lowered = raw_text.lower()
            break

    if raw_text_lowered.startswith("(assisted_draft)"):
        raw_text = raw_text[len("(assisted_draft)"):].lstrip()

    raw_text = raw_text.lstrip(":-— \n")

    lines: list[str] = []
    metadata_fragments = (
        "corrige esse",
        "corrigir esse",
        "como está esse",
        "como esta esse",
        "preciso saber",
        "versão atual",
        "versao atual",
        "número:",
        "numero:",
        "aprovada:",
        "notas:",
        "blocos da versão",
        "blocos da versao",
        "editar bloco",
    )

    for raw_line in raw_text.split("\n"):
        line = raw_line.strip()
        lowered_line = line.lower()

        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue

        if any(fragment in lowered_line for fragment in metadata_fragments):
            continue

        if "(assisted_draft)" in lowered_line or "— draft" in lowered_line or "- draft" in lowered_line:
            continue

        lines.append(line)

    cleaned = _clean_multiline_text("\n".join(lines), 6000)
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")
    return cleaned.strip()


def _iter_editor_context_strings(value: Any, *, max_items: int = 80) -> list[str]:
    collected: list[str] = []

    def visit(item: Any) -> None:
        if len(collected) >= max_items:
            return

        if item is None:
            return

        if isinstance(item, str):
            cleaned = _clean_multiline_text(item, 1200)
            if cleaned:
                collected.append(cleaned)
            return

        if isinstance(item, (int, float)):
            collected.append(str(item))
            return

        if isinstance(item, dict):
            for nested in item.values():
                visit(nested)
            return

        if isinstance(item, (list, tuple, set)):
            for nested in item:
                visit(nested)
            return

        for attr in ("case_number", "title", "summary", "description", "facts", "notes"):
            if hasattr(item, attr):
                visit(getattr(item, attr))

    visit(value)
    return collected


def _parse_brazilian_money(value: str) -> float | None:
    cleaned = str(value or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _format_brazilian_money(value: float) -> str:
    cents = int(round(value * 100))
    integer = cents // 100
    decimal = cents % 100
    integer_text = f"{integer:,}".replace(",", ".")
    return f"R$ {integer_text},{decimal:02d}"


def _known_amounts_section_from_texts(texts: list[str]) -> str:
    import re

    corpus = " ".join(texts)
    corpus = " ".join(corpus.replace("\n", " ").split())

    if not corpus:
        return ""

    lowered = corpus.lower()
    payment_docs_label = "comprovantes Pix" if "pix" in lowered else "comprovantes/documentos de pagamento"

    bullets: list[str] = []
    used_entries: set[str] = set()

    def add_bullet(key: str, text: str) -> None:
        if key in used_entries:
            return
        used_entries.add(key)
        bullets.append(text)

    installment_match = re.search(
        r"(\d+)\s+parcelas?\s+de\s+R\$\s*([\d.]+,\d{2})",
        corpus,
        flags=re.IGNORECASE,
    )

    installment_total: float | None = None
    if installment_match:
        quantity = int(installment_match.group(1))
        installment_value = _parse_brazilian_money(installment_match.group(2))
        if installment_value is not None:
            installment_total = quantity * installment_value
            add_bullet(
                "installments",
                f"Pagamentos parcelados informados: {quantity} parcelas de "
                f"{_format_brazilian_money(installment_value)}, total preliminar de "
                f"{_format_brazilian_money(installment_total)}, pendente de conferência dos "
                f"{payment_docs_label}.",
            )

    payment_total_match = re.search(
        r"(?:pagamentos?\s+(?:pix\s+)?informados?|valores?\s+pagos?|total\s+(?:pago|quitado|desembolsado)|desembolso\s+informado)\D{0,80}R\$\s*([\d.]+,\d{2})",
        corpus,
        flags=re.IGNORECASE,
    )

    if payment_total_match:
        payment_total = _parse_brazilian_money(payment_total_match.group(1))
        if payment_total is not None and (
            installment_total is None or abs(payment_total - installment_total) >= 0.01
        ):
            payment_label = "Pagamentos Pix informados" if "pix" in lowered else "Pagamentos informados"
            add_bullet(
                f"payment-total:{_format_brazilian_money(payment_total)}",
                f"{payment_label}: {_format_brazilian_money(payment_total)}, pendentes de conferência "
                f"quanto a datas, destinatário, vínculo com a negociação e integralidade dos "
                f"{payment_docs_label}.",
            )

    entry_match = None
    for pattern in (
        r"(?:entrada|valor\s+de\s+entrada|entrada\s+informada)\D{0,80}R\$\s*([\d.]+,\d{2})",
        r"R\$\s*([\d.]+,\d{2})\D{0,80}(?:como|a\s+t[íi]tulo\s+de|referente\s+a|referente\s+à)?\s*entrada",
    ):
        entry_match = re.search(pattern, corpus, flags=re.IGNORECASE)
        if entry_match:
            break

    if entry_match:
        entry_value = _parse_brazilian_money(entry_match.group(1))
        if entry_value is not None:
            add_bullet(
                f"entry:{_format_brazilian_money(entry_value)}",
                f"Entrada informada: {_format_brazilian_money(entry_value)}, pendente de conferência "
                "por contrato, recibos, mensagens, comprovantes, avaliação documental ou outros "
                "elementos mínimos de comprovação.",
            )

    economic_value_match = re.search(
        r"(?:valor\s+econ[oô]mico\s+preliminar|valor\s+econ[oô]mico\s+informado|total\s+econ[oô]mico\s+preliminar)\D{0,80}R\$\s*([\d.]+,\d{2})",
        corpus,
        flags=re.IGNORECASE,
    )

    if economic_value_match:
        economic_value = _parse_brazilian_money(economic_value_match.group(1))
        if economic_value is not None:
            add_bullet(
                f"economic:{_format_brazilian_money(economic_value)}",
                f"Valor econômico preliminar informado: {_format_brazilian_money(economic_value)}, "
                "sujeito à validação por contrato, comprovantes/documentos de pagamento, recibos, "
                "prestação de contas, memória de cálculo e revisão profissional.",
            )

    if not bullets:
        return ""

    joined = "\n".join(f"- {item}" for item in bullets)

    return f"""Valores preliminares já identificados no caso, sujeitos à conferência documental:

{joined}

Esses valores não substituem memória de cálculo, prestação de contas, liquidação dos pedidos ou revisão do advogado responsável."""

def _build_pedidos_valores_editor_revision(
    body: str,
    context: dict[str, Any] | None = None,
    raw_message: str = "",
) -> tuple[str, str]:
    problem = (
        "O bloco está viável, mas precisa deixar de ser apenas orientação genérica. A versão revisada deve organizar valor da causa, valores por pedido, memória de cálculo, valores comprovados e valores estimados, sempre com ressalva de conferência pelo advogado."
    )

    context_texts = [
        body,
        raw_message,
        *_iter_editor_context_strings(context or {}),
    ]
    known_amounts_section = _known_amounts_section_from_texts(context_texts)
    known_amounts_block = f"\n\n{known_amounts_section}" if known_amounts_section else ""

    revised = f"""I. Do valor da causa.

O valor da causa deverá ser definido pelo advogado responsável antes do protocolo, com base na soma dos pedidos economicamente apreciáveis, nos documentos disponíveis e na memória de cálculo revisada.

Valor da causa sugerido/preliminar: R$ [valor a calcular pelo advogado], sujeito à conferência dos documentos, comprovantes, contrato, recibos, pagamentos e demais elementos do caso.{known_amounts_block}

II. Dos valores a apurar por pedido.

Os valores deverão ser individualizados por pedido, sempre que possível, separando-se:

a) valor principal de eventual restituição, devolução ou recomposição patrimonial;
b) valores comprovadamente pagos ou desembolsados;
c) valores atribuídos a bens entregues, quando houver documento ou outro elemento mínimo de comprovação;
d) eventual saldo discutido, se houver prestação de contas ou demonstrativo;
e) eventuais danos materiais, desde que documentados;
f) eventual dano moral, se postulado, com valor estimativo a ser definido pelo advogado conforme a estratégia processual e a prova disponível.

III. Da memória de cálculo.

Caso ainda não exista memória de cálculo, recomenda-se elaborá-la antes do ajuizamento, indicando para cada pedido: origem do valor, documento correspondente, forma de cálculo, natureza liquidada ou estimada e eventual pendência de conferência.

IV. Dos valores estimados ou pendentes de liquidação.

Quando algum valor ainda depender de contrato, prestação de contas, exibição de documento, consulta oficial, perícia, prova testemunhal ou apuração posterior, o texto deverá indicar expressamente que se trata de valor estimado, preliminar ou pendente de liquidação.

V. Da cautela antes do protocolo.

Antes do protocolo definitivo, o advogado deverá revisar a coerência entre pedidos, causa de pedir, documentos anexados, memória de cálculo, valor da causa e eventual pedido de danos materiais ou morais, evitando valores fechados sem lastro documental suficiente."""
    return problem, revised.strip()



def _has_vehicle_editor_context(text: str) -> bool:
    corpus = str(text or "").lower()


    vehicle_markers = (
        "veículo",
        "veiculo",
        "revendedora",
        "detran",
        "retomada",
        "recolhimento",
        "busca e apreensão",
        "busca e apreensao",
    )
    vehicle_related_markers = (
        "suposto bloqueio",
        "bloqueio do veículo",
        "bloqueio do veiculo",
        "documentos do veículo",
        "documentos do veiculo",
        "localização atual do bem",
        "localizacao atual do bem",
        "guincho",
        "nota promissória",
        "nota promissoria",
        "parcelas via pix",
        "pagamentos via pix",
    )

    return any(marker in corpus for marker in vehicle_markers) or any(
        marker in corpus for marker in vehicle_related_markers
    )


def _build_pedidos_editor_revision(
    body: str,
    context: dict[str, Any] | None = None,
    raw_message: str = "",
) -> tuple[str, str]:
    original = _clean_editor_block_suggested_text(body, 6000)
    context_texts = [
        original,
        raw_message,
        *_iter_editor_context_strings(context or {}),
    ]
    lowered = " ".join(context_texts).lower()

    has_vehicle_context = _has_vehicle_editor_context(lowered)

    problem = (
        "O bloco precisa ajuste estrutural: há pontos de atenção e fundamentos misturados como se fossem pedidos. A versão revisada deve transformar a análise em requerimentos jurídicos objetivos, prudentes e condicionados à prova disponível."
    )

    if has_vehicle_context:
        revised = """I. Da tutela provisória, se presentes os requisitos legais.

Requer-se, se demonstrados a probabilidade do direito e o perigo de dano ou risco ao resultado útil do processo, a concessão da tutela provisória cabível para resguardar a utilidade do provimento final, especialmente quanto à preservação do veículo, esclarecimento de sua localização, impedimento de nova transferência indevida ou outra medida adequada ao caso concreto, conforme prova documental disponível.

II. Da exibição do contrato e documentos da negociação.

Requer-se que a parte ré apresente o contrato ou instrumento equivalente da negociação, eventuais notas promissórias, recibos, demonstrativo de parcelas, comprovantes de saldo alegado, documentos do veículo, registros de cobrança e demais documentos relacionados à compra, financiamento, parcelamento ou promessa de pagamento informada pelo cliente.

III. Da prestação de contas e apuração dos valores pagos.

Requer-se a apresentação de prestação de contas detalhada, com indicação dos valores recebidos, parcelas pagas, eventual saldo pendente, encargos aplicados, destinatário dos pagamentos e forma de imputação dos valores, incluindo a entrada informada mediante entrega de bens usados e os pagamentos realizados via Pix.

IV. Do esclarecimento formal do suposto bloqueio e da retomada/recolhimento do veículo.

Requer-se que a parte ré esclareça formalmente o motivo do alegado bloqueio do veículo e apresente eventual ordem judicial, busca e apreensão, restrição administrativa, registro no Detran, autorização contratual, comunicação prévia, termo de entrega, comprovante de guincho, localização atual do bem ou qualquer documento que justifique a retomada/recolhimento informado pelo cliente.

V. Da restituição do veículo ou devolução de valores, conforme apuração.

Requer-se, conforme o resultado da instrução probatória e da análise do advogado responsável, a restituição do veículo ao cliente ou, subsidiariamente, a devolução total ou parcial dos valores comprovadamente pagos, observada a apuração do contrato, dos pagamentos, do eventual saldo e das circunstâncias da retomada/recolhimento.

VI. Dos danos materiais e morais, se comprovados.

Requer-se a condenação da parte ré ao pagamento de danos materiais e, se cabível, danos morais, desde que comprovados o prejuízo, o nexo com a conduta discutida e os requisitos legais aplicáveis, evitando-se afirmação definitiva de dano ou ilicitude sem prova suficiente.

VII. Dos requerimentos processuais.

Requer-se a citação da parte ré, a produção de todos os meios de prova admitidos em direito, especialmente prova documental suplementar, testemunhal, depoimento pessoal, eventual prova pericial ou diligências necessárias, além dos demais requerimentos acessórios compatíveis com o rito, a causa de pedir e a estratégia processual definida pelo advogado responsável.

VIII. Da procedência.

Ao final, requer-se a procedência dos pedidos compatíveis com os fatos comprovados, a tese jurídica acolhida e a prova produzida, com revisão final do advogado responsável quanto à liquidez dos valores, adequação dos danos, pertinência da tutela e coerência entre pedidos, causa de pedir e documentos anexados."""
        return problem, revised.strip()

    revised = """I. Da tutela provisória, se cabível.

Requer-se, se presentes os requisitos legais, a concessão da tutela provisória adequada para resguardar a utilidade do provimento final.

II. Dos pedidos principais.

Requer-se a procedência dos pedidos compatíveis com os fatos narrados, a prova disponível, a tese jurídica sustentada e os documentos anexados, evitando-se requerimentos sem lastro probatório mínimo.

III. Da exibição de documentos e produção de prova.

Requer-se, quando necessário, a exibição de documentos, apresentação de informações, produção de prova documental, testemunhal, pericial ou outros meios admitidos em direito.

IV. Dos danos e demais consequências jurídicas.

Requer-se eventual condenação em danos materiais, danos morais, obrigação de fazer, restituição, devolução de valores ou outra medida cabível apenas quando houver suporte fático, documental e jurídico suficiente.

V. Dos requerimentos processuais.

Requer-se a citação da parte ré, a regular tramitação do feito e os demais requerimentos acessórios adequados ao rito e à estratégia processual definida pelo advogado responsável."""
    return problem, revised.strip()



def _build_fundamentacao_editor_revision(body: str) -> tuple[str, str]:
    original = _clean_editor_block_suggested_text(body, 6000)
    lowered = original.lower()

    has_consumer_context = any(
        marker in lowered
        for marker in (
            "consumidor",
            "código de defesa do consumidor",
            "cdc",
            "fornecedor",
            "revendedora",
            "produto",
            "serviço",
            "servico",
        )
    )
    has_vehicle_context = _has_vehicle_editor_context(lowered)

    problem = (
        "O bloco está viável, mas precisa ajuste estrutural: ele mistura fundamentação jurídica, estratégia operacional e lacunas probatórias, além de repetir pontos controvertidos. A versão revisada deve ligar fatos, prova mínima e tese jurídica com linguagem prudente."
    )

    if has_vehicle_context:
        revised = """I. Do cabimento da pretensão.

À luz do quadro fático narrado, a pretensão deve ser estruturada para apurar a regularidade da negociação, dos pagamentos realizados, da eventual existência de saldo pendente e da retomada/recolhimento do veículo informado pelo cliente. A análise deve permanecer condicionada à conferência dos documentos disponíveis e das provas que ainda serão obtidas.

II. Da relação de consumo e dos deveres de informação e transparência.

Em tese, a negociação com revendedora de veículos pode caracterizar relação de consumo, sujeitando o fornecedor aos deveres de informação clara, transparência, boa-fé objetiva e adequada prestação de contas. Assim, é juridicamente relevante apurar o conteúdo do contrato, notas promissórias, recibos, comprovantes de pagamento, dados do veículo e eventual justificativa formal apresentada para o suposto bloqueio ou recolhimento do bem.

III. Dos pagamentos, da entrada e da necessidade de apuração do valor econômico envolvido.

Os pagamentos informados por Pix, somados à entrada alegadamente realizada mediante entrega de bens usados, indicam possível lastro econômico relevante. Contudo, o valor total, eventual saldo, destinatário dos pagamentos, vínculo com a negociação e regularidade da cobrança devem ser confirmados por documentos, comprovantes, recibos, contrato, prestação de contas ou outros elementos idôneos.

IV. Da retomada/recolhimento do veículo e da controvérsia sobre o suposto bloqueio.

O relato de retomada ou recolhimento do veículo sob alegação de bloqueio exige apuração específica. Não se deve afirmar, sem prova suficiente, que houve ilegalidade definitiva, fraude, crime ou abuso. A versão final deve verificar se existiu ordem judicial, busca e apreensão, restrição administrativa, bloqueio no Detran, inadimplemento contratual, acordo entre as partes ou mera alegação comercial da revendedora.

V. Da exibição de documentos e da produção de prova.

Diante da perda da via física do contrato pelo cliente e da ausência de documentação completa apresentada até o momento, mostra-se relevante avaliar pedido de exibição de contrato, prestação de contas, demonstrativo de parcelas, comprovantes de eventual saldo, documento formal do suposto bloqueio e informações sobre a localização ou destino do veículo. A produção de prova deve ser direcionada para confirmar datas, valores, destinatários dos pagamentos, responsáveis pelo recolhimento e base documental da medida.

VI. Da tutela de urgência, restituição, devolução de valores e eventuais danos.

Pedidos de restituição do veículo, devolução total ou parcial de valores, indenização por danos materiais ou morais e tutela de urgência devem ser formulados com cautela e condicionados à prova disponível. A urgência dependerá de elementos concretos, como risco atual, posse ou localização do bem, impacto econômico, documentação mínima da negociação e verossimilhança das alegações.

VII. Síntese conclusiva.

A tese apresenta viabilidade preliminar moderada, desde que fortalecida por prova documental, conferência dos pagamentos, validação do suposto bloqueio e organização da linha fática. A fundamentação final deve evitar conclusões definitivas sem lastro probatório e manter linguagem técnica, prudente e condicionada à revisão profissional antes do protocolo."""
        return problem, revised.strip()

    if has_consumer_context:
        revised = """I. Do cabimento da pretensão.

À luz do quadro fático narrado, a pretensão deve ser estruturada para apurar a relação jurídica entre as partes, a conduta discutida, os deveres de informação, transparência e boa-fé, bem como os documentos disponíveis e as provas ainda pendentes de validação.

II. Da relação de consumo, se confirmada.

Quando os documentos e a natureza da relação indicarem vínculo entre consumidor e fornecedor, a fundamentação poderá invocar os deveres de informação adequada, transparência, boa-fé objetiva, segurança, prestação de contas e equilíbrio na relação contratual ou de prestação de serviço, sempre conforme a prova disponível e a revisão do advogado responsável.

III. Dos documentos, pagamentos e registros relevantes.

A versão final deve vincular os fundamentos aos documentos efetivamente disponíveis, como contrato, recibos, comprovantes de pagamento, mensagens, protocolos, notas fiscais, ordens de serviço, comunicações ou outros registros pertinentes, distinguindo prova já juntada de informação ainda pendente de confirmação.

IV. Das lacunas probatórias e da necessidade de exibição ou complementação documental.

Quando houver documentos em poder da parte contrária ou de terceiros, ou quando existirem lacunas relevantes, a fundamentação deve indicar a necessidade de exibição, complementação documental, prestação de informações, diligência ou outro meio adequado de esclarecimento.

V. Da cautela quanto a responsabilidade, danos e urgência.

Pedidos de obrigação de fazer, restituição, devolução de valores, indenização por danos materiais ou morais e tutela de urgência devem permanecer condicionados aos requisitos legais, ao nexo com os fatos comprovados e ao suporte documental mínimo, evitando-se conclusão definitiva sem lastro probatório suficiente.

VI. Síntese conclusiva.

A fundamentação é preliminar e deverá ser ajustada conforme a prova documental, as informações complementares, eventual resposta da parte contrária e a revisão técnica do advogado responsável antes do protocolo."""
        return problem, revised.strip()

    revised = """I. Do cabimento da pretensão.

À luz do quadro fático narrado, a demanda deve ser estruturada para tutelar o direito material afirmado, identificar a controvérsia central e relacionar os fatos relevantes às provas disponíveis e às provas ainda pendentes.

II. Dos fundamentos jurídicos aplicáveis.

A fundamentação deve indicar os regimes jurídicos possivelmente aplicáveis ao caso, conforme a natureza da relação entre as partes, o conteúdo dos documentos existentes e a prova mínima disponível. A versão final deve evitar enquadramentos definitivos antes da conferência documental.

III. Da prova mínima e das lacunas ainda pendentes.

A pretensão deve ser apoiada em documentos, comprovantes, registros, comunicações, testemunhas ou outros elementos idôneos. Quando houver lacuna relevante, o texto deve indicar expressamente que o ponto depende de validação, exibição de documento, diligência ou conferência posterior.

IV. Da cautela quanto a responsabilidade, danos e urgência.

Pedidos de indenização, responsabilização, obrigação de fazer, restituição, exibição de documentos ou tutela de urgência devem ser vinculados à prova disponível e aos requisitos legais aplicáveis. Não se deve afirmar culpa, ilicitude definitiva, dano consolidado ou urgência extrema sem suporte documental suficiente.

V. Síntese conclusiva.

A fundamentação é preliminar e deve ser ajustada conforme a prova produzida, os documentos anexados e a revisão técnica do advogado responsável antes do protocolo."""
    return problem, revised.strip()




def _build_provas_requerimentos_editor_revision(
    body: str,
    context: dict[str, Any] | None = None,
    raw_message: str = "",
) -> tuple[str, str]:
    context_texts = [
        body,
        raw_message,
        *_iter_editor_context_strings(context or {}),
    ]
    corpus = " ".join(context_texts).lower()

    has_vehicle_context = _has_vehicle_editor_context(corpus)

    problem = (
        "O bloco está viável, mas precisa deixar de ser genérico. A versão revisada deve separar provas já informadas, documentos pendentes, exibição de documentos, diligências e cautelas, sem tratar relato do cliente como prova documental já comprovada."
    )

    if has_vehicle_context:
        revised = """I. Das provas documentais já informadas pelo cliente.

Requer-se a juntada e conferência dos documentos que o cliente informa possuir, especialmente comprovantes Pix relacionados aos pagamentos parcelados, eventuais mensagens, recibos, registros de negociação, fotos, documentos do veículo ou outros elementos que demonstrem a relação entre as partes, os pagamentos realizados e as circunstâncias narradas.

A existência, autenticidade, integralidade e pertinência desses documentos deverão ser verificadas antes do protocolo, evitando-se tratar simples relato como prova documental já confirmada.

II. Das provas documentais pendentes de juntada ou conferência.

Devem ser identificados como pendentes, quando ainda não estiverem disponíveis nos autos internos do caso: contrato ou instrumento equivalente da negociação, notas promissórias, recibos da entrada informada, comprovantes integrais dos Pix, mensagens com a revendedora, documentos do veículo, eventual consulta ao Detran, comprovante de recolhimento, termo de entrega, comunicação prévia e qualquer documento relativo ao suposto bloqueio informado.

III. Da exibição de documentos pela parte ré.

Requer-se, se cabível conforme a estratégia processual, que a parte ré apresente o contrato ou instrumento de negociação, notas promissórias, demonstrativo de parcelas, prestação de contas, comprovantes de saldo alegado, documentos do veículo, registro do suposto bloqueio, ordem judicial ou administrativa eventualmente existente, comunicação enviada ao cliente, comprovante de guincho, termo de recolhimento/entrega e informação sobre a localização atual do bem.

IV. Das diligências e consultas úteis.

Requer-se a possibilidade de realização de diligências e consultas necessárias à elucidação dos fatos, especialmente para verificar a situação cadastral do veículo, eventual restrição administrativa ou judicial, histórico de propriedade, localização do bem, regularidade documental da negociação e vínculo entre os pagamentos informados e a parte ré.

V. Da prova testemunhal.

Requer-se a produção de prova testemunhal, caso existam pessoas que tenham presenciado a negociação, a entrega de bens usados como entrada, os pagamentos, a retirada/recolhimento do veículo, contatos com a revendedora ou outras circunstâncias relevantes. As testemunhas devem ser qualificadas e vinculadas objetivamente ao que sabem ou podem confirmar.

VI. Da cautela quanto à prova.

A narrativa do cliente deve ser tratada como relato inicial, pendente de confirmação por documentos, testemunhas, exibição de documentos, consultas oficiais ou outros meios admitidos em direito. Não se deve afirmar que houve bloqueio irregular, fraude, abuso, dano ou responsabilidade definitiva sem suporte probatório suficiente e revisão do advogado responsável.

VII. Dos requerimentos probatórios finais.

Requer-se a produção de todos os meios de prova em direito admitidos, especialmente documental suplementar, testemunhal, depoimento pessoal da parte ré, exibição de documentos, consultas oficiais, diligências e eventual prova técnica, conforme necessidade demonstrada no curso do processo e adequação ao rito escolhido."""
        return problem, revised.strip()

    revised = """I. Das provas documentais já informadas.

Requer-se a juntada e conferência dos documentos que a parte informa possuir, com indicação objetiva do que cada documento demonstra e de sua relação com os fatos narrados.

II. Das provas pendentes de juntada ou conferência.

Devem ser identificados expressamente os documentos, registros, mensagens, recibos, comprovantes, laudos, consultas, declarações ou outros elementos ainda pendentes de obtenção, conferência ou validação.

III. Da exibição de documentos e informações.

Requer-se, quando cabível, a exibição de documentos, registros, demonstrativos, contratos, comunicações ou informações que estejam em poder da parte contrária ou de terceiros e sejam relevantes para a apuração dos fatos.

IV. Das diligências e demais meios de prova.

Requer-se a realização das diligências úteis e a produção dos meios de prova admitidos em direito, incluindo prova documental suplementar, testemunhal, depoimento pessoal, perícia ou consulta técnica, conforme a natureza da controvérsia.

V. Da cautela quanto à prova.

A versão final deve distinguir fatos relatados, documentos efetivamente disponíveis, documentos pendentes e pontos que dependem de confirmação, evitando afirmar como provado aquilo que ainda exige validação documental, testemunhal, técnica ou profissional."""
    return problem, revised.strip()



def _build_checklist_final_editor_revision(body: str) -> tuple[str, str]:
    problem = (
        "O bloco está viável, mas precisa substituir o placeholder por um checklist operacional estruturado, genérico e útil para conferência antes do protocolo."
    )

    revised = """I. Conferência da qualificação das partes.

- Conferir nome completo, CPF/CNPJ, RG ou documento equivalente, estado civil, profissão, endereço completo e demais dados relevantes da parte autora.
- Conferir nome completo, CPF/CNPJ, endereço completo e demais dados relevantes da parte ré.
- Confirmar legitimidade ativa e passiva, representação, procuração, sucessão, espólio, litisconsórcio ou qualquer particularidade subjetiva do caso.

II. Conferência do advogado responsável e assinatura.

- Informar e conferir nome do advogado responsável.
- Informar e conferir OAB/UF.
- Conferir procuração, poderes, substabelecimento, contrato de honorários quando aplicável e autorização para protocolo.
- Informar local e data de assinatura.
- Confirmar assinatura da peça e dos documentos necessários.

III. Conferência da competência, rito e endereçamento.

- Confirmar comarca, foro, juízo competente, competência material e territorial.
- Conferir rito processual adequado, eventual prevenção, conexão, dependência ou distribuição por dependência.
- Revisar endereçamento antes do protocolo.

IV. Conferência dos fatos, fundamentos e pedidos.

- Confirmar se o resumo fático está coerente com documentos, relatos e provas disponíveis.
- Conferir se a fundamentação jurídica está adequada ao caso concreto e não contém afirmações sem suporte documental.
- Conferir se os pedidos estão claros, objetivos, compatíveis com a causa de pedir e condicionados à prova disponível.
- Conferir eventual tutela de urgência, obrigação de fazer, exibição de documentos, restituição, devolução de valores, indenização ou outro pedido específico.

V. Conferência do valor da causa e cálculos.

- Definir ou revisar valor da causa antes do protocolo.
- Conferir memória de cálculo, valores liquidados, valores estimados, documentos de pagamento, recibos, contratos, prestação de contas ou demais elementos econômicos.
- Evitar valor fechado sem lastro documental mínimo ou sem validação do advogado responsável.

VI. Conferência de documentos, anexos e provas.

- Conferir se todos os documentos essenciais foram juntados, nomeados e organizados.
- Separar documentos já disponíveis, documentos pendentes e documentos que deverão ser requeridos por exibição.
- Conferir procuração, documentos pessoais, comprovantes, contratos, recibos, mensagens, laudos, fotos, vídeos, protocolos, notificações, consultas oficiais e demais provas pertinentes ao caso.
- Confirmar se há necessidade de prova testemunhal, pericial, documental suplementar, depoimento pessoal, diligência ou consulta técnica.

VII. Conferência final antes do protocolo.

- Revisar ortografia, datas, nomes, números de documentos, valores, endereços, anexos e coerência geral da peça.
- Confirmar se a peça não afirma como comprovado aquilo que ainda depende de validação documental, testemunhal, técnica ou profissional.
- Confirmar se a versão final foi revisada e aprovada pelo advogado responsável antes do ajuizamento.
- Registrar internamente eventuais pendências que não impedem o protocolo, mas exigem acompanhamento posterior."""

    return problem, revised.strip()


def _build_editor_block_revision(
    label: str,
    body: str,
    context: dict[str, Any] | None = None,
    raw_message: str = "",
) -> tuple[str, str]:
    lowered_body = body.lower()
    lowered_label = label.lower()

    if lowered_label == "endereçamento" or lowered_label == "enderecamento":
        return (
            "Ajustar o placeholder da comarca e manter a advertência de conferência profissional, sem transformar o bloco em fato do caso.",
            (
                "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DO JUÍZO COMPETENTE DA COMARCA DE [COMARCA A CONFIRMAR PELO ADVOGADO].\n\n"
                "O advogado responsável deverá confirmar, antes do protocolo, a competência territorial, o juízo competente, eventual prevenção, o rito aplicável e a adequação da comarca conforme os documentos e a estratégia processual do caso."
            ),
        )

    if lowered_label == "resumo fático" or lowered_label == "resumo fatico":
        problem = (
            "O bloco está viável, mas deve permanecer narrativo. Estratégia, pedidos, indenização e tutela de urgência devem ficar nos blocos próprios."
        )
        revised = body

        for marker in ("O objetivo é montar", "O objetivo e montar"):
            idx = revised.find(marker)
            if idx >= 0:
                revised = revised[:idx].rstrip()
                break

        context_texts = [
            body,
            raw_message,
            *_iter_editor_context_strings(context or {}),
        ]
        has_vehicle_context = _has_vehicle_editor_context(" ".join(context_texts))

        if has_vehicle_context:
            narrative_close = (
                "A narrativa permanece sujeita à validação documental, especialmente quanto à existência e conteúdo do contrato, valores efetivamente pagos, destinatário dos Pix, eventual saldo pendente, motivo formal do suposto bloqueio e circunstâncias da retomada/recolhimento do veículo."
            )
        else:
            narrative_close = (
                "A narrativa permanece sujeita à validação documental e revisão profissional, especialmente quanto à confirmação dos fatos relatados, documentos disponíveis, datas relevantes, partes envolvidas, comunicações, valores informados, danos alegados e pontos ainda pendentes de prova."
            )

        if narrative_close.lower() not in revised.lower():
            revised = f"{revised.rstrip()}\n\n{narrative_close}"

        return problem, _format_resumo_fatico_paragraphs(revised)

    if lowered_label == "pedidos e valores estimados":
        return _build_pedidos_valores_editor_revision(
            body,
            context=context,
            raw_message=raw_message,
        )

    if lowered_label == "pedidos":
        return _build_pedidos_editor_revision(body, context=context, raw_message=raw_message)

    if lowered_label == "fundamentação" or lowered_label == "fundamentacao":
        return _build_fundamentacao_editor_revision(body)

    if lowered_label == "provas e requerimentos":
        return _build_provas_requerimentos_editor_revision(
            body,
            context=context,
            raw_message=raw_message,
        )

    if lowered_label == "checklist final":
        return _build_checklist_final_editor_revision(body)

    return (
        "Revisar o conteúdo como bloco editável da minuta, sem salvar como fato da Linha do Tempo.",
        body,
    )


def _looks_like_editor_block_prompt_text(text: str) -> bool:
    lowered = str(text or "").lower()
    if not lowered.strip():
        return False

    prompt_markers = (
        "reescreva somente o bloco",
        "entregue apenas o texto final",
        "texto final pronto para copiar e colar",
        "não traga checklist",
        "nao traga checklist",
        "não traga linha do tempo",
        "nao traga linha do tempo",
        "não invente dados",
        "nao invente dados",
        "quando faltar informação",
        "quando faltar informacao",
        "comece direto pelo texto do bloco",
        "gere todos os blocos",
        "todos os blocos principais",
        "blocos principais da minuta",
        "entregue somente os blocos finais",
        "separados por títulos exatamente assim",
        "separados por titulos exatamente assim",
        "não traga checklist operacional",
        "nao traga checklist operacional",
        "não misture pedidos",
        "nao misture pedidos",
        "comece direto pelo bloco 1",
    )

    return sum(1 for marker in prompt_markers if marker in lowered) >= 2


def _select_editor_block_source_body(
    *,
    case: Case,
    extracted_body: str,
    raw_message: str,
) -> str:
    candidate = _clean_text(extracted_body, 6000)
    if candidate and not _looks_like_editor_block_prompt_text(candidate):
        return candidate

    description = _clean_text(getattr(case, "description", ""), 6000)
    if description:
        return description

    title = _clean_text(getattr(case, "title", ""), 1000)
    if title:
        return title

    return candidate or _clean_text(raw_message, 6000)


def _extract_editor_labeled_fragment(
    source_text: str,
    start_markers: tuple[str, ...],
    stop_markers: tuple[str, ...],
    limit: int = 1800,
) -> str:
    raw = str(source_text or "")
    lowered = raw.lower()

    start_index = -1
    selected_marker = ""

    for marker in start_markers:
        index = lowered.find(marker.lower())
        if index >= 0 and (start_index < 0 or index < start_index):
            start_index = index
            selected_marker = marker

    if start_index < 0:
        return ""

    value_start = start_index + len(selected_marker)
    value_end = len(raw)

    for marker in stop_markers:
        index = lowered.find(marker.lower(), value_start)
        if index >= 0 and index < value_end:
            value_end = index

    return _clean_text(raw[start_index:value_end], limit)



def _cut_text_at_first_marker(text: str, markers: tuple[str, ...]) -> str:
    raw = str(text or "")
    lowered = raw.lower()

    cut_index = len(raw)
    for marker in markers:
        index = lowered.find(marker.lower())
        if index >= 0 and index < cut_index:
            cut_index = index

    return raw[:cut_index].strip()


def _remove_text_fragment_between_markers(
    text: str,
    start_markers: tuple[str, ...],
    stop_markers: tuple[str, ...],
) -> str:
    raw = str(text or "")
    lowered = raw.lower()

    start_index = -1
    selected_marker = ""

    for marker in start_markers:
        index = lowered.find(marker.lower())
        if index >= 0 and (start_index < 0 or index < start_index):
            start_index = index
            selected_marker = marker

    if start_index < 0:
        return raw

    value_start = start_index + len(selected_marker)
    stop_index = len(raw)

    for marker in stop_markers:
        index = lowered.find(marker.lower(), value_start)
        if index >= 0 and index < stop_index:
            stop_index = index

    if stop_index <= start_index:
        return raw

    return f"{raw[:start_index].rstrip()} {raw[stop_index:].lstrip()}".strip()


def _build_resumo_fatico_source_body(source_text: str) -> str:
    raw = _clean_text(source_text, 6000)
    if not raw:
        return ""

    cleaned = raw

    cleaned = _remove_text_fragment_between_markers(
        cleaned,
        ("Parte autora:", "Autor:", "Autora:"),
        (
            "Parte ré:",
            "Parte re:",
            "Ré:",
            "Re:",
            "Requerida:",
            "Requerido:",
            "O autor relata",
            "A autora relata",
            "O cliente relata",
            "A cliente relata",
            "A parte autora relata",
            "Segundo informado",
            "Fatos:",
            "Relato dos fatos:",
        ),
    )

    cleaned = _remove_text_fragment_between_markers(
        cleaned,
        ("Parte ré:", "Parte re:", "Ré:", "Re:", "Requerida:", "Requerido:"),
        (
            "O autor relata",
            "A autora relata",
            "O cliente relata",
            "A cliente relata",
            "A parte autora relata",
            "Segundo informado",
            "Fatos:",
            "Relato dos fatos:",
            "Como entrada",
            "Além da entrada",
            "Após",
            "No dia",
            "Em ",
        ),
    )

    cleaned = _cut_text_at_first_marker(
        cleaned,
        (
            "Provas existentes",
            "Provas existentes ou indicadas",
            "Provas indicadas",
            "Documentos existentes",
            "Documentos pendentes",
            "Documentos/provas",
            "Checklist",
            "Pontos a confirmar",
            "Pendências",
            "Testemunhas/depoentes",
            "Testemunhas",
            "Depoentes",
            "Pedidos a avaliar",
            "Pedidos possíveis",
            "Pedido pretendido",
            "Observação estratégica",
            "Observacao estrategica",
            "Pedidos:",
            "Comarca provável",
            "Vara competente",
            "Rito",
            "Valor da causa",
            "Tutela de urgência",
            "Estratégia jurídica",
        ),
    )

    cleaned = _clean_text(cleaned, 6000)
    return cleaned or raw


def _normalize_editor_detection_text(*values: Any) -> str:
    return " ".join(" ".join(str(value or "").lower().split()) for value in values)


def _is_cobranca_contratual_without_moral_damage(
    source_text: str,
    context: dict[str, Any] | None = None,
) -> bool:
    context = context or {}
    case_context = context.get("case_context") if isinstance(context, dict) else {}
    case_context = case_context if isinstance(case_context, dict) else {}

    normalized = _normalize_editor_detection_text(
        source_text,
        *(case_context.values()),
    )

    collection_markers = (
        "ação de cobrança",
        "acao de cobranca",
        "cobrança contratual",
        "cobranca contratual",
        "saldo contratual",
        "saldo devedor",
        "saldo inadimplido",
        "inadimplemento",
        "parcelas restantes",
        "dívida principal",
        "divida principal",
        "não foram pagas",
        "nao foram pagas",
    )
    no_moral_damage_markers = (
        "sem pedido de dano moral",
        "sem pedido de danos morais",
        "sem dano moral",
        "sem danos morais",
        "não pede dano moral",
        "nao pede dano moral",
        "não pleiteia dano moral",
        "nao pleiteia dano moral",
    )

    return any(marker in normalized for marker in collection_markers) and any(
        marker in normalized for marker in no_moral_damage_markers
    )


def _strip_editor_business_party_name(value: str) -> str:
    cleaned = _clean_text(value, 220)
    cleaned = re.sub(r"^(a|o)\s+empresa\s+", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" .,:;-")


def _extract_editor_business_parties_from_contract(source_text: str) -> tuple[str, str]:
    text = _clean_text(source_text, 6000)
    if not text:
        return "", ""

    patterns = (
        r"\bA empresa\s+(?P<author>.+?)\s+foi contratada pela empresa\s+(?P<defendant>.+?)\s+para\b",
        r"\bA empresa\s+(?P<author>.+?)\s+prestou serviços(?:\s+contratados)?\s+(?:para|à|a)\s+(?:empresa\s+)?(?P<defendant>.+?)(?:\.|,|\s+e\s+)",
    )

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue

        author = _strip_editor_business_party_name(match.group("author"))
        defendant = _strip_editor_business_party_name(match.group("defendant"))

        if author and defendant:
            return (
                f"Parte autora: {author}, qualificação completa, CNPJ, endereço, representante legal, contrato social e procuração a confirmar pelo advogado.",
                f"Parte ré: {defendant}, qualificação completa, CNPJ, endereço, representante legal, contrato social, dados cadastrais e documentos da relação contratual a confirmar pelo advogado.",
            )

    return "", ""

def _editor_text_has_any(normalized_text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in normalized_text for marker in markers)


def _build_editor_all_blocks_action_specialization(
    source_text: str,
    context: dict[str, Any] | None = None,
) -> tuple[str, str, str]:
    context = context or {}
    case_context = context.get("case_context") if isinstance(context, dict) else {}
    case_context = case_context if isinstance(case_context, dict) else {}

    normalized = _normalize_editor_detection_text(
        source_text,
        *(case_context.values()),
    )

    if _is_cobranca_contratual_without_moral_damage(source_text, context):
        return (
            "cobranca_contratual_without_moral_damage",
            (
                "A fundamentação preliminar deve se concentrar na cobrança contratual do saldo em aberto, "
                "considerando o inadimplemento da parte contratante, a execução integral ou substancial dos serviços, "
                "o pagamento parcial já realizado, o saldo contratual ainda em aberto e a necessidade de apuração do valor principal. "
                "Devem ser avaliados contrato, proposta, ordem de serviço, notas, comprovantes de pagamento, mensagens, planilha de cálculo, "
                "correção monetária, juros e multa contratual se prevista. "
                "A base legal específica, competência, rito, valor da causa e extensão final dos pedidos permanecem sujeitos à revisão profissional."
            ),
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a citação da parte ré, "
                "a condenação ao pagamento do saldo contratual inadimplido, com apuração do valor principal, correção monetária, juros, "
                "multa contratual se prevista, custas, honorários e demais encargos admitidos. "
                "Requer-se ainda a preservação e juntada das provas documentais disponíveis, especialmente contrato, proposta, ordem de serviço, "
                "notas, recibos, comprovantes de pagamento, mensagens e planilha de cálculo. "
                "Os pedidos finais, valor da causa, índice de correção, termo inicial dos juros e demais requerimentos devem ser definidos pelo advogado."
            ),
        )

    labor_markers = (
        "trabalhista",
        "reclamação trabalhista",
        "reclamacao trabalhista",
        "reclamante",
        "reclamada",
        "clt",
        "contrato de trabalho",
    )
    labor_health_risk_markers = (
        "insalubridade",
        "periculosidade",
        "calor intenso",
        "metal em fusão",
        "metal em fusao",
        "setor de fusão",
        "setor de fusao",
        "agente insalubre",
        "agentes insalubres",
        "exposição a calor",
        "exposicao a calor",
        "adicional de insalubridade",
        "adicional de periculosidade",
    )
    labor_health_evidence_markers = (
        "ppp",
        "ltcat",
        "pgr",
        "pcmso",
        "ficha de epi",
        "fichas de epi",
        "epi",
        "perícia técnica",
        "pericia tecnica",
        "laudo pericial",
        "medições ambientais",
        "medicoes ambientais",
        "engenheiro de segurança",
        "engenheiro de seguranca",
        "médico do trabalho",
        "medico do trabalho",
    )
    if _editor_text_has_any(normalized, labor_markers) and _editor_text_has_any(
        normalized, labor_health_risk_markers
    ):
        return (
            "labor_health_risk_premium_claim",
            (
                "A fundamentação preliminar deve se concentrar na reclamação trabalhista voltada ao adicional de insalubridade por exposição a calor "
                "em ambiente de trabalho, especialmente quando houver relato de setor de fusão, metal em fusão ou calor intenso. "
                "Deve ser avaliado, de forma subsidiária e prudente, eventual adicional de periculosidade apenas se os fatos e a prova técnica indicarem risco legalmente enquadrável. "
                "A análise depende de prova técnica, perícia, medições ambientais, PPP, LTCAT, PGR, PCMSO, ficha de EPI, registros de entrega, treinamento e uso de EPI, "
                "folhas de pagamento, documentos rescisórios e prova testemunhal. "
                "Devem ser avaliados grau de insalubridade, eficácia dos EPIs, habitualidade da exposição, período contratual, reflexos em férias acrescidas de um terço, "
                "13º salário, FGTS e verbas rescisórias, além de prescrição bienal e quinquenal. "
                "A base legal específica, competência da Justiça do Trabalho, rito, perícia, quesitos, liquidação e extensão final dos pedidos permanecem sujeitos à revisão do advogado responsável."
            ),
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a notificação da reclamada, "
                "a condenação ao pagamento de adicional de insalubridade por exposição a calor, no grau apurado por perícia técnica, "
                "e, subsidiariamente, a análise de adicional de periculosidade apenas se a prova técnica e documental confirmar hipótese legal aplicável. "
                "Requer-se a produção de prova pericial por profissional habilitado, com avaliação do ambiente de trabalho, agente calor, medições ou análise técnica retroativa, "
                "eficácia dos EPIs, habitualidade da exposição e formulação de quesitos pelo advogado. "
                "Requer-se também a exibição, preservação ou juntada dos documentos essenciais da relação de emprego e de saúde e segurança do trabalho, especialmente PPP, LTCAT, PGR, PCMSO, "
                "ficha de EPI, registros de entrega e treinamento de EPI, folhas de pagamento, contrato ou CTPS, TRCT e documentos rescisórios. "
                "Requer-se, se comprovado o direito, o pagamento dos reflexos cabíveis em férias acrescidas de um terço, 13º salário, FGTS e verbas rescisórias. "
                "Os pedidos finais, grau do adicional, base de cálculo, reflexos, critérios de cálculo, honorários, justiça gratuita se cabível, perícia e demais requerimentos devem ser definidos pelo advogado responsável."
            ),
        )

    labor_hours_markers = (
        "jornada superior",
        "jornada superior à registrada",
        "jornada superior a registrada",
        "horas extras",
        "hora extra",
        "diferenças de horas extras",
        "diferencas de horas extras",
        "intervalo intrajornada",
        "supressão parcial de intervalo",
        "supressao parcial de intervalo",
        "supressão total de intervalo",
        "supressao total de intervalo",
        "controle de ponto",
        "controles de ponto",
        "cartões de ponto",
        "cartoes de ponto",
        "registros de jornada",
    )
    if _editor_text_has_any(normalized, labor_markers) and _editor_text_has_any(
        normalized, labor_hours_markers
    ):
        return (
            "labor_hours_interval_claim",
            (
                "A fundamentação preliminar deve se concentrar na reclamação trabalhista relacionada à jornada de trabalho, "
                "horas extras, eventual divergência entre jornada efetiva e registros formais, supressão total ou parcial do intervalo intrajornada "
                "e reflexos trabalhistas decorrentes. "
                "Devem ser avaliados controles de ponto, holerites, TRCT, extrato analítico do FGTS, mensagens com gestor, documentos rescisórios, "
                "eventuais normas coletivas, depoimento do reclamante, preposto da empresa e testemunhas. "
                "A análise deve considerar diferenças de horas extras, adicional aplicável, reflexos em DSR, férias acrescidas de um terço, 13º salário, FGTS, "
                "verbas rescisórias e demais parcelas estritamente compatíveis com os fatos relatados e os documentos disponíveis. "
                "A base legal específica, competência da Justiça do Trabalho, rito, prescrição, liquidação e extensão final dos pedidos permanecem sujeitos à revisão do advogado responsável."
            ),
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a notificação da reclamada, "
                "o reconhecimento das diferenças de jornada comprovadas, a condenação ao pagamento de horas extras e do intervalo intrajornada suprimido, "
                "com adicional legal, contratual ou normativo aplicável, conforme apuração em liquidação. "
                "Requer-se também o pagamento dos reflexos cabíveis em DSR, férias acrescidas de um terço, 13º salário, FGTS e verbas rescisórias, "
                "além da juntada e preservação dos documentos essenciais da relação de emprego, especialmente controles de ponto, holerites, TRCT, extrato analítico do FGTS, "
                "mensagens com gestor e demais registros de jornada. "
                "Os pedidos finais, valores, reflexos, critérios de cálculo, honorários, justiça gratuita se cabível e demais requerimentos devem ser definidos pelo advogado responsável."
            ),
        )


    family_markers = (
        "família",
        "familia",
        "vara de família",
        "vara de familia",
        "ação de alimentos",
        "acao de alimentos",
        "alimentos",
        "pensão alimentícia",
        "pensao alimenticia",
        "guarda",
        "convivência",
        "convivencia",
        "visitas",
        "regulamentação de visitas",
        "regulamentacao de visitas",
        "menor",
        "criança",
        "crianca",
        "adolescente",
        "genitor",
        "genitora",
        "melhor interesse do menor",
        "certidão de nascimento",
        "certidao de nascimento",
    )
    family_support_guardianship_markers = (
        "alimentos",
        "pensão alimentícia",
        "pensao alimenticia",
        "despesas do menor",
        "despesas da criança",
        "despesas da crianca",
        "renda do genitor",
        "renda da genitora",
        "renda dos genitores",
        "guarda",
        "convivência",
        "convivencia",
        "visitas",
        "regulamentação de visitas",
        "regulamentacao de visitas",
        "melhor interesse do menor",
        "documentos da criança",
        "documentos da crianca",
        "informações escolares",
        "informacoes escolares",
        "saúde da criança",
        "saude da crianca",
    )
    if _editor_text_has_any(normalized, family_markers) and _editor_text_has_any(
        normalized, family_support_guardianship_markers
    ):
        family_support_markers = (
            "ação de alimentos",
            "acao de alimentos",
            "fixação de alimentos",
            "fixacao de alimentos",
            "revisão de alimentos",
            "revisao de alimentos",
            "exoneração de alimentos",
            "exoneracao de alimentos",
            "pensão alimentícia",
            "pensao alimenticia",
            "alimentos provisórios",
            "alimentos provisorios",
            "alimentos definitivos",
            "pedido de alimentos",
            "pretende alimentos",
        )
        family_guardianship_markers = (
            "ação de guarda",
            "acao de guarda",
            "guarda",
            "guarda unilateral",
            "guarda compartilhada",
        )
        family_visitation_markers = (
            "convivência",
            "convivencia",
            "visitas",
            "regulamentação de visitas",
            "regulamentacao de visitas",
            "regulamentação de convivência",
            "regulamentacao de convivencia",
        )

        has_support_request = _editor_text_has_any(normalized, family_support_markers)
        has_guardianship_request = _editor_text_has_any(normalized, family_guardianship_markers)
        has_visitation_request = _editor_text_has_any(normalized, family_visitation_markers)

        request_parts = [
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, "
                "requer-se a citação ou intimação da parte requerida."
            )
        ]

        if has_support_request:
            request_parts.append(
                "Requer-se a fixação, revisão ou adequação de alimentos provisórios e definitivos, "
                "conforme as necessidades da criança ou adolescente e a capacidade econômica dos responsáveis."
            )

        if has_guardianship_request:
            request_parts.append(
                "Requer-se a definição, revisão ou regularização da guarda, unilateral ou compartilhada conforme o caso, "
                "com observância da rotina de cuidados e do melhor interesse da criança ou adolescente."
            )

        if has_visitation_request:
            request_parts.append(
                "Requer-se a regulamentação do regime de convivência familiar, com definição de visitas, férias, "
                "datas comemorativas, comunicação entre os responsáveis e eventual supervisão quando houver suporte fático."
            )

        request_parts.append(
            "Requer-se a preservação e juntada dos documentos essenciais, especialmente certidão de nascimento, "
            "documentos pessoais, comprovante de residência, comprovantes de despesas, documentos escolares, "
            "documentos médicos, comprovantes de renda, mensagens e demais elementos pertinentes."
        )
        request_parts.append(
            "Segredo de justiça, intervenção do Ministério Público, estudo psicossocial quando pertinente, "
            "valor da causa e demais requerimentos devem ser definidos pelo advogado responsável, "
            "observando o melhor interesse da criança ou adolescente."
        )

        pedidos = " ".join(request_parts)

        return (
            "family_support_guardianship_claim",
            (
                "A fundamentação preliminar deve se concentrar na demanda de Família relacionada a alimentos, guarda, "
                "convivência familiar ou regulamentação de visitas, sempre com foco no melhor interesse da criança ou adolescente "
                "e na proteção integral. Devem ser avaliados certidão de nascimento, documentos pessoais dos responsáveis, "
                "comprovante de residência, despesas ordinárias e extraordinárias do menor, necessidades de saúde, educação, "
                "alimentação, moradia, transporte e rotina de cuidados. Também devem ser examinadas a capacidade econômica "
                "dos genitores, renda formal ou informal, participação de cada responsável nos cuidados, histórico de convivência, "
                "eventuais acordos prévios, mensagens, comprovantes de pagamento e documentos escolares ou médicos. "
                "A competência da Vara de Família, a urgência, a intervenção do Ministério Público e a estratégia final "
                "devem ser definidas pelo advogado responsável conforme os fatos relatados e os documentos disponíveis."
            ),
            pedidos,
        )

    vehicle_markers = (
        "veículo",
        "veiculo",
        "automóvel",
        "automovel",
        "revendedora",
        "automóveis",
        "automoveis",
        "renavam",
        "placa",
    )
    vehicle_dispute_markers = (
        "recolheu",
        "retomou",
        "retomada",
        "tomou",
        "bloqueio",
        "restrição",
        "restricao",
        "exibição de contrato",
        "exibicao de contrato",
        "comprovantes pix",
        "parcelas",
    )
    if _editor_text_has_any(normalized, vehicle_markers) and _editor_text_has_any(
        normalized, vehicle_dispute_markers
    ):
        return (
            "consumer_vehicle_contract_display_restitution",
            (
                "A fundamentação preliminar deve se concentrar na relação contratual e de consumo envolvendo aquisição de veículo, "
                "pagamentos realizados, documentos contratuais pendentes, eventual restrição ou bloqueio informado e possível recolhimento ou retenção do bem. "
                "Devem ser avaliados comprovantes de pagamento, contrato, recibos, conversas, documentos do veículo, placa, RENAVAM, consulta de restrição, "
                "eventual ordem judicial, justificativa apresentada pela parte ré e a viabilidade de exibição de documentos, restituição do veículo, "
                "regularização da situação ou perdas e danos. "
                "A base legal específica, competência, rito, urgência e extensão dos pedidos permanecem sujeitos à revisão profissional."
            ),
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a citação da parte ré, "
                "a exibição do contrato, recibos, documentos do veículo, justificativa do bloqueio ou restrição e demais documentos essenciais da negociação. "
                "Requer-se também a análise da restituição do veículo, regularização da situação do bem ou indenização material equivalente, conforme a prova documental e a estratégia confirmada. "
                "Devem ser juntados e preservados comprovantes Pix, mensagens, consultas oficiais, documentos do veículo e demais registros disponíveis. "
                "Tutela de urgência, busca do bem, obrigação específica, perdas e danos, valor da causa, custas e honorários devem ser definidos pelo advogado apenas se houver suporte documental suficiente."
            ),
        )

    obligation_markers = (
        "obrigação de fazer",
        "obrigacao de fazer",
        "obrigação de não fazer",
        "obrigacao de nao fazer",
        "cumprimento de obrigação",
        "cumprimento de obrigacao",
        "regularização",
        "regularizacao",
    )
    if _editor_text_has_any(normalized, obligation_markers):
        return (
            "obligation_to_do_or_not_do",
            (
                "A fundamentação preliminar deve se concentrar na obrigação específica indicada no caso, no vínculo jurídico que a sustenta, "
                "no descumprimento atribuído à parte ré, na utilidade prática do provimento pretendido e na necessidade de prazo razoável para cumprimento. "
                "Devem ser avaliados documentos que comprovem a obrigação, comunicações prévias, tentativas de solução, urgência concreta, risco de dano e eventual cabimento de multa diária. "
                "A base legal específica, competência, rito e extensão final dos pedidos permanecem sujeitos à revisão profissional."
            ),
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a citação da parte ré, "
                "a determinação de cumprimento da obrigação específica indicada no caso, em prazo a ser definido pelo juízo, "
                "com eventual fixação de multa diária se houver suporte fático e jurídico. "
                "Requer-se a juntada e preservação dos documentos, mensagens, notificações, protocolos e demais provas do descumprimento. "
                "Pedidos de indenização, tutela de urgência, astreintes, perdas e danos, custas e honorários devem ser definidos pelo advogado conforme a prova disponível."
            ),
        )

    damage_markers = (
        "dano moral",
        "danos morais",
        "dano material",
        "danos materiais",
        "indenização",
        "indenizacao",
        "ato ilícito",
        "ato ilicito",
    )
    no_moral_damage_markers = (
        "sem pedido de dano moral",
        "sem pedido de danos morais",
        "sem dano moral",
        "sem danos morais",
    )
    if _editor_text_has_any(normalized, damage_markers) and not _editor_text_has_any(
        normalized, no_moral_damage_markers
    ):
        return (
            "civil_damages_claim",
            (
                "A fundamentação preliminar deve se concentrar na conduta atribuída à parte ré, no dano alegado, "
                "no nexo entre os fatos e o prejuízo, na extensão dos danos materiais ou morais indicados e na prova mínima disponível. "
                "Devem ser avaliados documentos, comunicações, comprovantes, registros administrativos, eventuais perdas mensuráveis e circunstâncias concretas que sustentem a indenização. "
                "A base legal específica, competência, rito, quantificação e extensão final dos pedidos permanecem sujeitos à revisão profissional."
            ),
            (
                "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a citação da parte ré, "
                "a apuração da responsabilidade pelos fatos narrados e a condenação ao pagamento de indenização por danos materiais e/ou morais, "
                "somente nos limites comprovados pelos documentos e pela estratégia definida pelo advogado. "
                "Requer-se a preservação e juntada das provas disponíveis, incluindo comprovantes, mensagens, registros, laudos, recibos e demais documentos pertinentes. "
                "Valor da causa, quantificação do dano, correção monetária, juros, custas, honorários e eventual tutela devem ser definidos pelo advogado."
            ),
        )

    return (
        "generic_prudent",
        (
            "A fundamentação preliminar deverá ser avaliada pelo advogado responsável à luz dos fatos relatados, "
            "dos documentos disponíveis, da natureza da relação jurídica, dos deveres de informação, boa-fé, "
            "transparência, cumprimento contratual, prestação de contas e eventual responsabilidade civil ou restituitória, "
            "conforme o enquadramento jurídico confirmado após análise documental. "
            "As teses jurídicas, a base legal específica, o rito, a competência, a urgência e a extensão dos pedidos permanecem sujeitos à revisão profissional."
        ),
        (
            "Diante do exposto, e sem prejuízo de adequação pelo advogado responsável, requer-se a citação da parte ré, "
            "a exibição dos documentos essenciais da relação jurídica, a prestação de contas ou esclarecimentos formais sobre os fatos controvertidos, "
            "a apuração dos valores envolvidos, a preservação e juntada das provas disponíveis, e a adoção das medidas necessárias para recompor o direito alegado pelo Autor, "
            "inclusive restituição, obrigação de fazer ou não fazer e eventual indenização por danos materiais e/ou morais, caso haja lastro documental suficiente. "
            "Os pedidos finais, tutela de urgência, valor da causa, correção monetária, juros, custas, honorários e demais requerimentos devem ser definidos pelo advogado."
        ),
    )


def _editor_all_blocks_ready_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_message = str(message or "")
    extracted_body = _extract_editor_block_body(raw_message)
    source_body = _select_editor_block_source_body(
        case=case,
        extracted_body=extracted_body,
        raw_message=raw_message,
    )

    editor_context = {
        **(context or {}),
        "case_context": {
            "case_number": getattr(case, "case_number", ""),
            "title": getattr(case, "title", ""),
            "description": getattr(case, "description", ""),
            "legal_area": getattr(case, "legal_area", ""),
            "action_type": getattr(case, "action_type", ""),
        },
    }

    business_parte_autora, business_parte_re = _extract_editor_business_parties_from_contract(source_body)

    _, enderecamento = _build_editor_block_revision(
        "Endereçamento",
        "",
        context=editor_context,
        raw_message=raw_message,
    )
    resumo_source_body = _build_resumo_fatico_source_body(source_body)
    _, resumo_fatico = _build_editor_block_revision(
        "Resumo Fático",
        resumo_source_body,
        context=editor_context,
        raw_message=raw_message,
    )

    parte_autora = _extract_editor_labeled_fragment(
        source_body,
        ("Parte autora:", "Autor:", "Autora:"),
        ("Parte ré:", "Parte re:", "Ré:", "Re:", "O autor relata", "A autora relata", "Fatos:"),
    )
    parte_re = _extract_editor_labeled_fragment(
        source_body,
        ("Parte ré:", "Parte re:", "Ré:", "Re:", "Requerida:", "Requerido:"),
        ("O autor relata", "A autora relata", "Fatos:", "Como entrada", "Provas existentes", "Provas:"),
    )

    qualificacao = "\n\n".join(
        item
        for item in (
            parte_autora or business_parte_autora or "Parte autora: a confirmar, conforme documentos pessoais, comprovante de endereço, procuração e cadastro do caso.",
            parte_re or business_parte_re or "Parte ré: a confirmar, conforme contrato, comprovantes, cadastro público, documentos da relação jurídica e revisão do advogado.",
        )
        if item
    )

    action_specialization_kind, fundamentacao, pedidos = _build_editor_all_blocks_action_specialization(
        source_body,
        editor_context,
    )

    family_action_specialization_kinds = {
        "family_support_guardianship_claim",
    }
    if action_specialization_kind in family_action_specialization_kinds:
        enderecamento = (
            "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DA VARA DE FAMÍLIA DE [LOCALIDADE A CONFIRMAR PELO ADVOGADO].\n\n"
            "O advogado responsável deverá confirmar, antes do protocolo, a competência da Vara de Família, "
            "a localidade competente, eventual prevenção, o segredo de justiça, a participação do Ministério Público quando cabível "
            "e a adequação do rito conforme os documentos e a estratégia processual do caso."
        )
        qualificacao = "\n\n".join(
            item
            for item in (
                "Requerente: a confirmar, conforme documentos pessoais, comprovante de endereço, procuração e cadastro do caso.",
                "Requerido(a): a confirmar, conforme documentos pessoais, endereço conhecido, vínculo familiar, capacidade econômica e revisão do advogado.",
                "Criança/adolescente: a confirmar, conforme certidão de nascimento, documentos escolares, documentos de saúde e demais elementos do caso.",
            )
            if item
        )

    labor_action_specialization_kinds = {
        "labor_health_risk_premium_claim",
        "labor_hours_interval_claim",
    }
    if action_specialization_kind in labor_action_specialization_kinds:
        enderecamento = (
            "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DA VARA DO TRABALHO DE [LOCALIDADE A CONFIRMAR PELO ADVOGADO].\n\n"
            "O advogado responsável deverá confirmar, antes do protocolo, a competência territorial da Justiça do Trabalho, "
            "a Vara do Trabalho competente, eventual prevenção, o rito trabalhista aplicável, o local da prestação de serviços, "
            "o domicílio das partes e a adequação do endereçamento conforme os documentos e a estratégia processual do caso."
        )

        def _labor_party_label(
            fragment: str | None,
            source_labels: tuple[str, ...],
            target_label: str,
            fallback: str,
        ) -> str:
            if not fragment:
                return fallback
            cleaned = fragment.strip()
            lowered = cleaned.lower()
            for source_label in source_labels:
                if lowered.startswith(source_label.lower()):
                    return f"{target_label}:{cleaned[len(source_label):]}"
            return f"{target_label}: {cleaned}"

        qualificacao = "\n\n".join(
            item
            for item in (
                _labor_party_label(
                    parte_autora or business_parte_autora,
                    ("Parte autora:", "Autor:", "Autora:"),
                    "Reclamante",
                    "Reclamante: a confirmar, conforme documentos pessoais, comprovante de endereço, CTPS, contrato de trabalho, procuração e cadastro do caso.",
                ),
                _labor_party_label(
                    parte_re or business_parte_re,
                    ("Parte ré:", "Parte re:", "Ré:", "Re:", "Requerida:", "Requerido:"),
                    "Reclamada",
                    "Reclamada: a confirmar, conforme contrato de trabalho, CTPS, TRCT, folhas de pagamento, documentos da relação de emprego, cadastro público e revisão do advogado.",
                ),
            )
            if item
        )

    if "advogado responsável" not in fundamentacao.lower():
        fundamentacao = (
            fundamentacao.rstrip()
            + " O advogado responsável deverá confirmar o enquadramento jurídico, a base legal específica, "
            "o rito, a competência e a extensão dos pedidos antes do protocolo."
        )

    if "fatos relatados" not in fundamentacao.lower():
        fundamentacao = (
            fundamentacao.rstrip()
            + " A análise deve permanecer vinculada aos fatos relatados e aos documentos disponíveis no caso."
        )

    if "documentos essenciais" not in pedidos.lower():
        pedidos = (
            pedidos.rstrip()
            + " Requer-se também a exibição, preservação ou juntada dos documentos essenciais da relação jurídica discutida."
        )

    if "pedidos finais" not in pedidos.lower():
        pedidos = (
            pedidos.rstrip()
            + " Os pedidos finais, valor da causa, custas, honorários, eventual urgência e demais requerimentos "
            "devem ser definidos pelo advogado responsável."
        )

    if action_specialization_kind == "family_support_guardianship_claim":
        provas = (
            "Protesta-se pela produção dos meios de prova pertinentes à demanda de Família, especialmente certidão de nascimento, "
            "documentos pessoais dos responsáveis, comprovante de residência, comprovantes das despesas da criança ou adolescente, "
            "comprovantes de renda formal ou informal dos genitores, documentos escolares, boletins, matrículas, laudos, receitas, "
            "atestados e demais documentos médicos. "
            "Requer-se também a preservação e juntada de mensagens entre os responsáveis, comprovantes de pagamentos de alimentos, "
            "recibos relacionados à rotina de cuidados, documentos de convivência familiar e demais elementos que demonstrem "
            "as necessidades da criança ou adolescente, a capacidade econômica dos responsáveis e a participação de cada genitor nos cuidados. "
            "Quando cabível, requer-se estudo psicossocial, avaliação interdisciplinar, oitiva das partes, prova testemunhal sobre a rotina familiar, "
            "expedição de ofícios para obtenção de informações escolares, médicas ou de renda, exibição de documentos e juntada posterior de novos elementos. "
            "Devem ser preservados o segredo de justiça, a intervenção do Ministério Público nas hipóteses legais "
            "e o melhor interesse da criança ou adolescente."
        )
    elif action_specialization_kind == "labor_health_risk_premium_claim":
        provas = (
            "Protesta-se pela produção de prova técnica pericial por profissional habilitado em saúde e segurança do trabalho, "
            "com avaliação do ambiente laboral, setor de fusão, exposição a calor, metal em fusão, medições ambientais, "
            "critérios técnicos aplicáveis, grau de insalubridade, eventual risco enquadrável como periculosidade e eficácia dos EPIs. "
            "Requer-se a formulação de quesitos periciais pelo advogado responsável, a possibilidade de assistente técnico, "
            "a inspeção do local de trabalho ou análise técnica retroativa quando cabível, e a manifestação expressa sobre habitualidade, intensidade e neutralização do agente de risco. "
            "Requer-se também a exibição, preservação e juntada de PPP, LTCAT, PGR, PCMSO, laudos ambientais, ficha de EPI, registros de entrega e treinamento de EPI, "
            "folhas de pagamento, contrato ou CTPS, TRCT, documentos rescisórios, descrição de função e demais documentos de saúde e segurança do trabalho. "
            "Protesta-se ainda pela prova testemunhal de colegas do setor de fusão, supervisores ou demais pessoas que possam descrever rotina, tempo de exposição, calor, uso e eficácia dos EPIs, "
            "sem prejuízo de depoimento pessoal da reclamada, juntada posterior de novos documentos e expedição de ofícios quando necessário."
        )
    else:
        provas = (
            "Protesta-se pela produção de todos os meios de prova em direito admitidos, especialmente documentos já disponíveis, comprovantes de pagamento, contratos, recibos, mensagens, prints, áudios, vídeos, consultas oficiais, registros administrativos, depoimento pessoal da parte ré, oitiva de testemunhas a confirmar e demais provas que se mostrarem necessárias. "
            "Requer-se, se pertinente e após revisão do advogado, a expedição de ofícios, a exibição de documentos e a juntada posterior de novos elementos que confirmem os fatos narrados."
        )

    fechamento = (
        "A presente minuta é preliminar e deve ser revisada pelo advogado responsável antes de qualquer protocolo. "
        "Devem ser confirmados dados formais das partes, comarca, competência, rito, valor da causa, documentos essenciais, provas mínimas, datas relevantes, estratégia processual, pedidos finais e eventual urgência. "
        "Onde houver informação incompleta, divergente ou sem documento, deve constar a expressão “a confirmar” ou equivalente prudente."
    )

    blocks = (
        ("BLOCO 1 — Endereçamento", enderecamento),
        ("BLOCO 2 — Qualificação das partes", qualificacao),
        ("BLOCO 3 — Resumo Fático", resumo_fatico),
        ("BLOCO 4 — Fundamentação preliminar", fundamentacao),
        ("BLOCO 5 — Pedidos", pedidos),
        ("BLOCO 6 — Provas e requerimentos", provas),
        ("BLOCO 7 — Fechamento e conferência final", fechamento),
    )

    rewritten_input = "\n\n".join(
        f"{title}\n\n{_clean_editor_block_suggested_text(body, 5000)}"
        for title, body in blocks
    )

    return {
        "case_id": case.id,
        "assistant_mode": "editor_all_blocks_ready",
        "summary": "Texto pronto para colar nos principais blocos da minuta.",
        "rewritten_input": _clean_editor_block_suggested_text(rewritten_input, 12000),
        "suggested_actions": [],
        "next_steps": [],
        "warnings": [],
        "disclaimer": "",
        "metadata": {
            "source": "case_operational_assistant_editor_all_blocks_ready_v1",
            "action_specialization_kind": action_specialization_kind,
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "timeline_items_considered": len(timeline),
            "blocks": [title for title, _ in blocks],
        },
    }



def _editor_block_correction_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
    *,
    pure_text_only: bool = False,
) -> dict[str, Any]:
    raw_message = str(message or "")
    lowered = raw_message.lower()
    block_label = _detect_editor_block_label(lowered)
    block_body = _extract_editor_block_body(raw_message)
    if pure_text_only:
        block_body = _select_editor_block_source_body(
            case=case,
            extracted_body=block_body,
            raw_message=raw_message,
        )
    editor_context = {
        **(context or {}),
        "case_context": {
            "case_number": getattr(case, "case_number", ""),
            "title": getattr(case, "title", ""),
            "description": getattr(case, "description", ""),
            "legal_area": getattr(case, "legal_area", ""),
            "action_type": getattr(case, "action_type", ""),
        },
    }
    problem, revised_text = _build_editor_block_revision(
        block_label,
        block_body,
        context=editor_context,
        raw_message=raw_message,
    )

    if not revised_text:
        revised_text = "[Cole aqui o texto revisado do bloco após validar os dados do caso.]"

    if pure_text_only:
        return {
            "case_id": case.id,
            "assistant_mode": "editor_block_pure_text",
            "summary": f"Texto pronto para colar no bloco {block_label}.",
            "rewritten_input": _clean_editor_block_suggested_text(revised_text, 6000),
            "suggested_actions": [],
            "next_steps": [],
            "warnings": [],
            "disclaimer": "",
            "metadata": {
                "source": "case_operational_assistant_editor_block_pure_text_v1",
                "provider": "fallback",
                "case_number": _clean_text(getattr(case, "case_number", "")),
                "timeline_items_considered": len(timeline),
                "block_label": block_label,
            },
        }

    suggested_text = _clean_editor_block_suggested_text(
        f"""Veredito: viável, com ajuste no bloco editável.

Bloco: {block_label}.

Problema principal:
{problem}

Texto sugerido para substituir:
{revised_text}

Ação agora:
Aplicar o texto sugerido no campo editável "{block_label}" do Editor/minuta. Não salvar este conteúdo na Linha do Tempo e não abrir Anexos/provas automaticamente, salvo se houver pedido explícito sobre documentos ou prova.""",
        6000,
    )

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": f"Veredito: revisar no Editor/minuta o bloco {block_label}.",
        "rewritten_input": "",
        "suggested_actions": [
            {
                "destination": "editor_minuta",
                "label": f"Revisar bloco: {block_label}",
                "suggested_text": suggested_text,
                "reason": "O texto enviado é um bloco editável de minuta; deve ser corrigido no Editor/minuta, não organizado como fato do caso.",
                "priority": "alta",
            }
        ],
        "next_steps": [
            f"Aplicar a sugestão no bloco editável {block_label}.",
            "Não salvar este conteúdo na Linha do Tempo; criar Checklist ou Anexo apenas se houver pendência/prova real específica.",
        ],
        "warnings": [
            "Não transformar bloco de minuta em fato cronológico.",
            "Não exportar para PDF antes de revisar todos os blocos editáveis.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_editor_block_correction_routing_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "timeline_items_considered": len(timeline),
        },
    }


def _is_review_validation_message(lowered: str) -> bool:
    text = f" {lowered.strip()} "
    if not text.strip():
        return False

    review_markers = (
        "confere se",
        "confira se",
        "verifica se",
        "verifique se",
        "ve se",
        "vê se",
        "olha se",
        "olhe se",
        "esta bom",
        "está bom",
        "ficou bom",
        "ta bom",
        "tá bom",
        "precisa mudar",
        "precisa alterar",
        "tem que mudar",
        "tem algo errado",
        "algo errado",
        "esta coerente",
        "está coerente",
        "ficou coerente",
        "esta correto",
        "está correto",
        "ficou correto",
        "revisa",
        "revise",
        "validar",
        "valida",
        "valide",
        "analise se",
        "melhorar esse texto",
        "melhorar essa análise",
        "melhorar essa analise",
        "falta algo",
        "faltou algo",
    )
    content_markers = (
        "análise",
        "analise",
        "resumo",
        "pontos de atenção",
        "pontos de atencao",
        "próximos passos",
        "proximos passos",
        "risco",
        "diagnóstico",
        "diagnostico",
        "dossiê",
        "dossie",
        "linha do tempo",
        "checklist",
        "anexos",
        "provas",
        "caso",
        "processo",
        "peça",
        "peca",
        "minuta",
        "texto",
    )

    has_review_marker = any(marker in text for marker in review_markers)
    has_content_marker = any(marker in text for marker in content_markers)

    return has_review_marker and has_content_marker


def _review_validation_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    text = _clean_text(message, 2500)
    lowered = text.lower()

    mentions_analysis = any(
        marker in lowered
        for marker in ("análise", "analise", "diagnóstico", "diagnostico", "risco", "pontos de atenção", "pontos de atencao")
    )
    mentions_timeline = "linha do tempo" in lowered or "timeline" in lowered
    mentions_evidence = any(marker in lowered for marker in ("anexo", "anexos", "prova", "provas", "documento", "documentos", "comprovante"))
    mentions_dossier = "dossiê" in lowered or "dossie" in lowered
    mentions_draft = any(marker in lowered for marker in ("peça", "peca", "minuta", "petição", "peticao"))

    must_change: list[str] = []
    keep_items: list[str] = []
    optional_improvements: list[str] = []

    if (
        "analisado automaticamente em modo de contingência" in lowered
        or "analisado automaticamente em modo de contingencia" in lowered
    ):
        must_change.append(
            "Localização provável: bloco Análise > Resumo técnico, na frase de abertura. Observação: esse bloco pode ser somente leitura/gerado automaticamente. Onde está: 'analisado automaticamente em modo de contingência'. Sugestão para próxima versão revisada: 'analisado em caráter operacional preliminar'. Motivo: fica mais claro, profissional e evita parecer falha interna do sistema."
        )
    elif "modo de contingência" in lowered or "modo de contingencia" in lowered:
        must_change.append(
            "Localização provável: trecho em que aparece a expressão técnica indicada. Onde está: 'modo de contingência'. Troque por: 'análise operacional preliminar'. Motivo: linguagem mais clara para usuário comum e aplicável a qualquer caso."
        )

    if "analisado automaticamente" in lowered and not (
        "analisado automaticamente em modo de contingência" in lowered
        or "analisado automaticamente em modo de contingencia" in lowered
    ):
        optional_improvements.append(
            "Localização provável: frase de abertura, resumo técnico ou trecho de apresentação da análise. Observação: se o bloco for somente leitura, não tente editar diretamente. Onde está: 'analisado automaticamente'. Sugestão para próxima versão revisada: 'análise operacional gerada pelo sistema'. Motivo: fica melhor para cliente ou usuário final, mantendo a necessidade de revisão profissional."
        )

    if any(marker in lowered for marker in ("suposto", "alega", "cliente informa", "pendente de validação", "pendente de validacao")):
        keep_items.append(
            "Manter a linguagem cautelosa como 'suposto', 'alega', 'cliente informa' e 'pendente de validação', pois isso evita conclusão sem prova."
        )

    if any(marker in lowered for marker in ("sem afirmar crime", "sem afirmar culpa", "não afirmar crime", "nao afirmar crime", "não afirmar culpa", "nao afirmar culpa")):
        keep_items.append(
            "Manter o alerta para não afirmar crime, culpa ou irregularidade definitiva sem prova suficiente."
        )

    if "nível de risco: médio" in lowered or "nivel de risco: medio" in lowered or "risco: médio" in lowered or "risco: medio" in lowered:
        keep_items.append(
            "Manter risco médio se ainda faltam documentos essenciais e não há prova validada de urgência extrema; ajustar apenas se surgir fato novo relevante."
        )
    elif "risco" in lowered:
        optional_improvements.append(
            "Conferir o nível de risco: manter se estiver compatível com urgência, prova disponível e impacto prático; ajustar se houver fato novo relevante."
        )

    if any(marker in lowered for marker in ("crime", "culpa", "ilegalidade", "fraude", "golpe")):
        optional_improvements.append(
            "Conferir linguagem sensível: não afirmar crime, culpa, fraude, golpe ou ilegalidade definitiva sem prova suficiente e revisão profissional."
        )

    has_required_change = bool(must_change)

    if not keep_items:
        keep_items.append(
            "Manter os trechos que estejam objetivos, prudentes, coerentes com o caso e ligados a documentos, pendências ou próximos passos."
        )

    if not optional_improvements:
        optional_improvements.append(
            "Sem melhoria opcional específica detectada; se quiser uma redação mais bonita, peça para gerar uma versão revisada."
        )

    change_section = (
        "O que mudar:\n" + "\n".join(f"- {item}" for item in must_change)
        if has_required_change
        else "O que mudar:\n- Nada obrigatório no conteúdo. Ajustes de redação são opcionais."
    )

    recommended_changes_text = (
        f"Veredito: {'viável, com ajuste pequeno.' if has_required_change else 'viável.'}\n"
        f"Precisa mexer? {'Sim, apenas no ponto indicado abaixo.' if has_required_change else 'Não há alteração obrigatória de conteúdo.'}\n\n"
        + change_section
        + "\n\nO que manter:\n"
        + "\n".join(f"- {item}" for item in keep_items[:3])
        + "\n\nAção agora:\n"
        "- Manter/salvar se o conteúdo estiver fiel aos documentos. "
        "Se o ajuste estiver em bloco somente leitura, registrar no Dossiê interno ou gerar nova versão revisada. "
        "Marcar no Checklist apenas as pendências reais de documento, prova, data, valor ou validação externa."
    )

    suggestions: list[dict[str, str]] = [
        _suggestion(
            "dossie",
            "Veredito curto de viabilidade",
            recommended_changes_text,
            "Pedidos como 'está viável?' ou 'precisa mexer?' devem responder com veredito, mudança necessária e ação agora, sem repetir o texto inteiro do usuário.",
            "alta",
        ),
        _suggestion(
            "checklist",
            "Marcar pendências reais",
            "Registrar no Checklist apenas o que depender de contrato, documento, data, valor, testemunha, consulta oficial ou validação externa.",
            "A revisão deve gerar pendência operacional apenas quando houver lacuna real, risco de linguagem ou falta de prova.",
            "alta",
        ),
    ]

    if mentions_evidence:
        suggestions.append(
            _suggestion(
                "anexos",
                "Conferir lastro documental",
                "Verificar se cada conclusão relevante tem documento, prova real ou pendência expressa. Se não tiver, usar termos como 'cliente informa', 'alega', 'suposto' e 'pendente de validação'.",
                "A revisão deve proteger o caso contra afirmações fortes demais sem prova anexada.",
                "alta",
            )
        )

    if mentions_timeline:
        suggestions.append(
            _suggestion(
                "linha_do_tempo",
                "Conferir fatos cronológicos",
                "Verificar se os fatos principais estão em ordem cronológica e se cada item tem prova relacionada ou pendência indicada.",
                "A análise fica melhor quando a narrativa, o checklist e os anexos conversam entre si.",
                "normal",
            )
        )

    if (mentions_dossier or mentions_draft) and not mentions_analysis:
        suggestions.append(
            _suggestion(
                "dossie",
                "Atualizar visão operacional",
                "Depois de revisar os ajustes, atualizar o Dossiê interno para consolidar diagnóstico, pendências, riscos e próximos passos.",
                "O Dossiê deve refletir a versão mais confiável do caso antes de análise jurídica ou minuta.",
                "normal",
            )
        )

    if mentions_analysis:
        summary = (
            "Veredito: viável, com ajuste pequeno."
            if has_required_change
            else "Veredito: viável. Não há alteração obrigatória de conteúdo."
        )
    else:
        summary = (
            "Veredito: viável, com ajuste pequeno."
            if has_required_change
            else "Veredito: manter se estiver claro, prudente e coerente com o módulo correto."
        )

    next_steps = [
        "Aplicar apenas o ajuste obrigatório indicado, se houver. Se o bloco for somente leitura, registrar a observação no Dossiê interno ou gerar nova versão revisada.",
        "Manter o conteúdo se ele estiver fiel aos documentos, aos fatos preenchidos e às pendências registradas.",
        "Marcar no Checklist somente pendências reais de contrato, comprovante, consulta oficial, testemunha, valor, data ou validação externa.",
    ]

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": summary,
        "rewritten_input": "",
        "suggested_actions": suggestions[:4],
        "next_steps": next_steps,
        "warnings": [
            "Não transformar pedido de revisão em fato da Linha do Tempo.",
            "Não afirmar crime, culpa, ilegalidade definitiva, valor fechado ou responsabilidade sem prova suficiente.",
            "Quando faltar documento ou validação, pedir ajuste ou marcar pendência em vez de inventar informação.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_review_validation_routing_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "timeline_items_considered": len(timeline),
        },
    }


def _fallback_response(case: Case, message: str, context: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    text = _clean_text(message, 2500)
    lowered = text.lower()

    if _is_editor_all_blocks_ready_message(lowered):
        return _editor_all_blocks_ready_response(
            case=case,
            message=message,
            context=context,
            timeline=timeline,
        )

    if _is_editor_block_pure_text_message(lowered) or _is_editor_block_correction_message(lowered):
        return _editor_block_correction_response(
            case=case,
            message=message,
            context=context,
            timeline=timeline,
            pure_text_only=_is_editor_block_pure_text_message(lowered),
        )

    if _is_review_validation_message(lowered):
        return _review_validation_response(
            case=case,
            message=text,
            context=context,
            timeline=timeline,
        )

    if _is_natural_next_step_message(lowered):
        return _natural_next_step_response(
            case=case,
            message=text,
            context=context,
            timeline=timeline,
        )

    requested_guidance_modules = _requested_guidance_modules(lowered)
    if requested_guidance_modules:
        return _module_guidance_response(
            case=case,
            message=text,
            context=context,
            timeline=timeline,
            modules=requested_guidance_modules,
        )

    if _is_evidence_availability_message(lowered):
        return _evidence_availability_response(
            case=case,
            message=text,
            context=context,
            timeline=timeline,
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

    if _is_editor_all_blocks_ready_message(cleaned_message.lower()) or _is_editor_block_pure_text_message(cleaned_message.lower()):
        return fallback

    try:
        raw = request_structured_analysis(_build_prompt(case=case, message=cleaned_message, context=context, timeline=timeline))
    except LLMClientError:
        return fallback
    except Exception:
        return fallback

    return _normalize_response(raw=raw, fallback=fallback, case_id=case.id)
