from app.api.v1.routes.editable_documents import (
    _build_content_viability_assisted_claims,
    _build_content_viability_proof_items,
)


def test_content_viability_claims_convert_issues_into_concrete_requests():
    raw_issues = [
        "Relação de consumo com revendedora de veículos, exigindo validação do fornecedor, contrato, negociação e documentos do veículo.",
        "Pagamentos relevantes por Pix e entrada com bens usados, exigindo conferência de valores, destinatário dos Pix, notas promissórias e eventual saldo discutido.",
        "Retomada/recolhimento do veículo sob alegação de suposto bloqueio, sem documentação clara apresentada até o momento.",
    ]

    claims = _build_content_viability_assisted_claims(
        normalized_area="consumidor",
        case_search_text=(
            "Cliente relata compra de veículo em revendedora, pagamento por Pix, "
            "entrada com bens usados, contrato perdido, notas promissórias, "
            "suposto bloqueio e retomada/recolhimento do veículo."
        ),
        issues=raw_issues,
        controverted_points=raw_issues,
        proof_checklist=[
            "Anexar comprovantes Pix.",
            "Obter contrato, notas promissórias, recibos e prestação de contas.",
            "Conferir documento formal do suposto bloqueio e consulta Detran.",
        ],
        next_steps=[
            "Avaliar exibição de documentos, restituição do veículo ou devolução de valores."
        ],
    )

    joined_claims = "\n".join(claims)

    assert claims
    assert all(claim.startswith("Requer-se") for claim in claims)

    assert "exibição do contrato" in joined_claims
    assert "apuração dos valores pagos" in joined_claims
    assert "justificativa formal" in joined_claims
    assert "restituição do bem" in joined_claims or "devolução total ou parcial" in joined_claims

    assert raw_issues[0] not in claims
    assert raw_issues[1] not in claims
    assert raw_issues[2] not in claims
    assert "exigindo validação do fornecedor" not in joined_claims
    assert "exigindo conferência de valores" not in joined_claims


def test_content_viability_proof_items_separate_existing_pending_and_requested_proof():
    proof_items = _build_content_viability_proof_items(
        case_search_text=(
            "Cliente informa comprovantes Pix, contrato perdido, notas promissórias, "
            "suposto bloqueio, consulta Detran pendente e retomada/recolhimento do veículo."
        ),
        issues=[],
        controverted_points=[],
        proof_checklist=[
            "Comprovantes Pix.",
            "Contrato e notas promissórias.",
            "Documento do suposto bloqueio.",
            "Prova da retomada/recolhimento.",
        ],
        next_steps=[],
    )

    joined_proofs = "\n".join(proof_items)

    assert "comprovantes de pagamento" in joined_proofs
    assert "contratos, notas promissórias" in joined_proofs
    assert "suposto bloqueio" in joined_proofs
    assert "quem retomou ou recolheu o bem" in joined_proofs
    assert "já está provado" in joined_proofs
    assert "pendente" in joined_proofs
    assert "exibição" in joined_proofs
