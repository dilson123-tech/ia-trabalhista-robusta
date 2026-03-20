from app.modules.appeals_reactions import (
    AppealDeadline,
    AppealDraftRef,
    AppealStrategyItem,
    AppealsReactionsService,
    DecisionPoint,
    JudicialDecision,
)


def _build_sample_decision() -> JudicialDecision:
    return JudicialDecision(
        area="trabalhista",
        case_id=10,
        tenant_id=20,
        decision_type="sentenca",
        title="Sentença parcialmente improcedente",
        summary="A decisão rejeitou parte dos pedidos formulados pela reclamante.",
        decision_date="2026-03-19",
        unfavorable_points=[
            DecisionPoint(
                key="fgts_denied",
                title="FGTS indeferido",
                description="Pedido de diferenças de FGTS foi rejeitado.",
                outcome="unfavorable",
            ),
            DecisionPoint(
                key="moral_damage_denied",
                title="Dano moral indeferido",
                description="Pedido de indenização por dano moral foi rejeitado.",
                outcome="unfavorable",
            ),
        ],
        metadata={"judge": "Juízo da 1ª Vara do Trabalho"},
    )


def test_build_state_from_decision_creates_reaction_state() -> None:
    service = AppealsReactionsService()
    decision = _build_sample_decision()

    state = service.build_state_from_decision(decision)

    assert state.area == "trabalhista"
    assert state.case_id == 10
    assert state.tenant_id == 20
    assert state.source_decision is decision
    assert state.metadata["decision_type"] == "sentenca"
    assert state.metadata["unfavorable_points_count"] == 2


def test_add_deadline_strategy_and_draft_to_reaction_state() -> None:
    service = AppealsReactionsService()
    state = service.build_state_from_decision(_build_sample_decision())

    state = service.add_deadline(
        state,
        AppealDeadline(
            key="ro_deadline",
            title="Prazo para Recurso Ordinário",
            due_date="2026-03-27",
            status="pending",
        ),
    )

    state = service.add_strategy_item(
        state,
        AppealStrategyItem(
            key="attack_fgts_basis",
            title="Impugnar fundamentos do indeferimento de FGTS",
            description="Atacar a fundamentação probatória e pedir reforma do capítulo.",
            target_point_keys=["fgts_denied"],
            priority="high",
        ),
    )

    state = service.add_appeal_draft(
        state,
        AppealDraftRef(
            document_type="recurso_ordinario",
            title="Minuta inicial do Recurso Ordinário",
            status="draft",
            version=1,
        ),
    )

    assert len(state.deadlines) == 1
    assert state.deadlines[0].key == "ro_deadline"

    assert len(state.strategy_items) == 1
    assert state.strategy_items[0].key == "attack_fgts_basis"
    assert state.strategy_items[0].target_point_keys == ["fgts_denied"]

    assert len(state.appeal_drafts) == 1
    assert state.appeal_drafts[0].document_type == "recurso_ordinario"


def test_add_strategy_item_rejects_unknown_decision_point() -> None:
    service = AppealsReactionsService()
    state = service.build_state_from_decision(_build_sample_decision())

    try:
        service.add_strategy_item(
            state,
            AppealStrategyItem(
                key="invalid_target",
                title="Item inválido",
                description="Aponta para capítulo inexistente.",
                target_point_keys=["chapter_that_does_not_exist"],
            ),
        )
    except ValueError as exc:
        assert "was not found" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown decision point")


def test_summarize_reaction_returns_consolidated_payload() -> None:
    service = AppealsReactionsService()
    state = service.build_state_from_decision(_build_sample_decision())

    state = service.add_deadline(
        state,
        AppealDeadline(
            key="embargos_deadline",
            title="Prazo para Embargos de Declaração",
            due_date="2026-03-24",
            status="pending",
        ),
    )

    state = service.add_strategy_item(
        state,
        AppealStrategyItem(
            key="attack_moral_damage_basis",
            title="Atacar fundamentos do dano moral",
            description="Explorar omissão na valoração da prova oral.",
            target_point_keys=["moral_damage_denied"],
            priority="high",
        ),
    )

    state = service.add_appeal_draft(
        state,
        AppealDraftRef(
            document_type="embargos_declaracao",
            title="Minuta base de embargos",
            status="draft",
            version=1,
        ),
    )

    summary = service.summarize_reaction(state)

    assert summary["area"] == "trabalhista"
    assert summary["case_id"] == 10
    assert summary["decision_type"] == "sentenca"
    assert len(summary["unfavorable_points"]) == 2
    assert summary["deadlines"][0]["key"] == "embargos_deadline"
    assert summary["strategy_items"][0]["key"] == "attack_moral_damage_basis"
    assert summary["appeal_drafts"][0]["document_type"] == "embargos_declaracao"
