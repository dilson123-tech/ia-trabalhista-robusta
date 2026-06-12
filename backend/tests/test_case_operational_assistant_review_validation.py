from types import SimpleNamespace

from app.services.case_operational_assistant import (
    _review_validation_response,
)


def _fake_case():
    return SimpleNamespace(id=428, case_number="VEICULO-QUINTINO-PIX-001")


def _action_text(response: dict) -> str:
    parts: list[str] = [
        response.get("summary") or "",
        response.get("rewritten_input") or "",
        "\n".join(response.get("next_steps") or []),
        "\n".join(response.get("warnings") or []),
    ]

    for action in response.get("suggested_actions") or []:
        parts.extend(
            [
                action.get("destination") or "",
                action.get("label") or "",
                action.get("suggested_text") or "",
                action.get("reason") or "",
            ]
        )

    return "\n".join(parts)


def test_review_validation_is_concise_and_does_not_echo_full_input():
    pasted_analysis = (
        "como esta esse preciso saber se ta viavel ou precisa mexer\n"
        "Caso analisado: 428 | Análise: 362\n"
        "Resumo técnico: Processo VEICULO-QUINTINO-PIX-001 analisado automaticamente em modo de contingência, "
        "considerando a área jurídica consumidor e o tipo de ação Exibição de contrato / restituição de veículo "
        "ou valores / indenização. Foram identificados 5 pontos relevantes.\n"
        "Pontos de atenção: Relação de consumo com revendedora de veículos. Pagamentos relevantes por Pix. "
        "Retomada/recolhimento do veículo sob alegação de suposto bloqueio, sem documentação clara.\n"
        "Próximos passos: Anexar comprovantes Pix, solicitar contrato, notas promissórias, prestação de contas, "
        "documento do suposto bloqueio e justificativa formal da revendedora."
    )

    response = _review_validation_response(
        case=_fake_case(),
        message=pasted_analysis,
        context={},
        timeline=[],
    )

    output = _action_text(response)

    assert response["rewritten_input"] == ""
    assert response["summary"].startswith("Veredito:")
    assert "Veredito curto de viabilidade" in output
    assert "Precisa mexer?" in output
    assert "analisado em caráter operacional preliminar" in output

    assert "Texto corrigido/sugerido" not in output
    assert pasted_analysis not in output
    assert len(response["suggested_actions"]) <= 4
    assert all(action.get("destination") != "linha_do_tempo" for action in response["suggested_actions"])


def test_review_validation_keeps_timeline_suggestion_when_user_mentions_timeline():
    response = _review_validation_response(
        case=_fake_case(),
        message=(
            "confere se a linha do tempo ficou boa no caso 428. "
            "Quero saber se está coerente com a análise e se precisa mexer."
        ),
        context={},
        timeline=[
            {"title": "Compra do veículo"},
            {"title": "Pagamentos por Pix"},
        ],
    )

    assert response["rewritten_input"] == ""
    assert any(action.get("destination") == "linha_do_tempo" for action in response["suggested_actions"])
