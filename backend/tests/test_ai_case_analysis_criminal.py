from app.services.ai_case_analysis import _fallback_analysis


def test_criminal_fallback_analysis_uses_criminal_language_without_labor_leak():
    payload = _fallback_analysis(
        case_number="CRIM-002",
        title="Pedido de liberdade provisória em prisão em flagrante",
        description=(
            "Cliente foi preso em flagrante, passou por audiência de custódia "
            "e há discussão sobre liberdade provisória e medidas cautelares."
        ),
        legal_area="criminal",
        action_type="liberdade_provisoria",
    )

    joined = " ".join(
        [
            payload["summary"],
            *payload["issues"],
            *payload["next_steps"],
        ]
    ).lower()

    assert payload["legal_area"] == "criminal"
    assert payload["action_type"] == "liberdade_provisoria"
    assert payload["risk_level"] in {"medium", "high"}
    assert "liberdade provisória" in joined or "liberdade provisoria" in joined
    assert "prisão" in joined or "prisao" in joined
    assert "fgts" not in joined
    assert "justiça do trabalho" not in joined
    assert "contrato de trabalho" not in joined
