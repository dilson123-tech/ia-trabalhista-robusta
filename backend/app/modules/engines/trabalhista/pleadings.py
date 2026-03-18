from __future__ import annotations


def build_peticao_inicial_trabalhista_sections(payload: dict | None = None) -> list[dict]:
    data = payload or {}

    reclamante = data.get("reclamante_nome") or "NOME DO RECLAMANTE"
    reclamada = data.get("reclamada_nome") or "NOME DA RECLAMADA"
    contrato = data.get("contrato_resumo") or "Descrever vínculo, função, período e jornada."
    fatos = data.get("fatos") or "Descrever os fatos principais do caso trabalhista."
    fundamentos = data.get("fundamentos") or (
        "Indicar fundamentos jurídicos aplicáveis, verbas postuladas e violações alegadas."
    )
    pedidos = data.get("pedidos") or (
        "Listar pedidos de forma objetiva, com reflexos e requerimentos finais."
    )
    provas = data.get("provas") or (
        "Indicar documentos, testemunhas e demais meios de prova pretendidos."
    )
    valor_causa = data.get("valor_causa") or "Informar valor estimado da causa."

    return [
        {
            "key": "partes",
            "title": "Das partes",
            "content": (
                f"Reclamante: {reclamante}. "
                f"Reclamada: {reclamada}. "
                "Qualificação completa a ser detalhada no intake guiado."
            ),
        },
        {
            "key": "contrato_trabalho",
            "title": "Do contrato de trabalho",
            "content": contrato,
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
            "content": (
                "Requer a citação da parte reclamada, a procedência dos pedidos, "
                "a produção de todas as provas admitidas e demais cominações legais."
            ),
        },
    ]
