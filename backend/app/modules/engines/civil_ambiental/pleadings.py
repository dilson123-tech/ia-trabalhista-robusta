from __future__ import annotations


def build_peticao_inicial_civil_sections(payload: dict | None = None) -> list[dict]:
    data = payload or {}

    autor = data.get("autor_nome") or data.get("reclamante_nome") or "NOME DA PARTE AUTORA"
    reu = data.get("reu_nome") or data.get("reclamada_nome") or "NOME DA PARTE RÉ"
    fatos = data.get("fatos") or data.get("description") or "Descrever os fatos principais do caso cível."
    fundamentos = data.get("fundamentos") or (
        "Indicar os fundamentos jurídicos aplicáveis, a relação obrigacional, o inadimplemento "
        "ou a lesão ao direito alegado, com base legal e jurisprudencial pertinente."
    )
    pedidos = data.get("pedidos") or (
        "Listar os pedidos de forma objetiva, incluindo condenação principal, correção monetária, "
        "juros, custas, honorários e demais requerimentos cabíveis."
    )
    provas = data.get("provas") or (
        "Indicar contrato, notas, mensagens, documentos, testemunhas e demais meios de prova pertinentes."
    )
    valor_causa = data.get("valor_causa") or "Informar o valor atualizado da causa."
    fechamento = data.get("fechamento") or (
        "Requer a citação da parte ré, a total procedência dos pedidos, a produção de todas as provas "
        "admitidas em direito e as demais cominações legais."
    )

    return [
        {
            "key": "partes",
            "title": "Das partes",
            "content": (
                f"Parte autora: {autor}. "
                f"Parte ré: {reu}. "
                "Qualificação completa a ser detalhada no preenchimento final da peça."
            ),
        },
        {
            "key": "fatos",
            "title": "Dos fatos",
            "content": fatos,
        },
        {
            "key": "fundamentos",
            "title": "Dos fundamentos jurídicos",
            "content": fundamentos,
        },
        {
            "key": "pedidos",
            "title": "Dos pedidos",
            "content": pedidos,
        },
        {
            "key": "provas",
            "title": "Das provas",
            "content": provas,
        },
        {
            "key": "valor_causa",
            "title": "Do valor da causa",
            "content": valor_causa,
        },
        {
            "key": "fechamento",
            "title": "Requerimentos finais",
            "content": fechamento,
        },
    ]
