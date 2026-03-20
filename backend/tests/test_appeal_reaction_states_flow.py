from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_appeal_{uuid.uuid4().hex[:8]}@example.com",
        "password": "dev",
        "role": "admin",
    }

    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": "test-seed-token"},
    )
    assert r_seed.status_code == 200
    assert r_seed.json()["ok"] is True

    r_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": seed_payload["username"],
            "password": seed_payload["password"],
        },
    )
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_appeal_reaction_state_authenticated_flow(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"APPEAL-{uuid.uuid4().hex[:8]}",
        "title": "Caso de teste do módulo recursal",
        "description": "Validação da persistência/API de decisões, prazos, estratégia e minuta recursal.",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_state_payload = {
        "case_id": case_id,
        "area": "trabalhista",
        "source_decision": {
            "decision_type": "sentenca",
            "title": "Sentença parcialmente procedente",
            "summary": "A sentença acolheu parte dos pedidos e rejeitou FGTS e dano moral.",
            "decision_date": "2026-03-20",
            "metadata": {
                "source": "test_appeal_reaction_states_flow",
            },
            "unfavorable_points": [
                {
                    "key": "fgts_denied",
                    "title": "FGTS indeferido",
                    "description": "O pedido de FGTS foi rejeitado por ausência de prova documental suficiente.",
                    "outcome": "unfavorable",
                    "legal_effect": "reduz condenação",
                    "metadata": {"chapter": "fgts"},
                },
                {
                    "key": "moral_damage_denied",
                    "title": "Dano moral indeferido",
                    "description": "A sentença afastou o dano moral por entender ausente prova robusta.",
                    "outcome": "unfavorable",
                    "legal_effect": "afasta indenização",
                    "metadata": {"chapter": "moral_damage"},
                },
            ],
        },
        "metadata": {
            "source": "test_appeal_reaction_states_flow",
        },
    }

    r_create_state = client.post(
        "/api/v1/appeal-reaction-states",
        json=create_state_payload,
        headers=headers,
    )
    assert r_create_state.status_code == 200
    created_state = r_create_state.json()

    assert created_state["case_id"] == case_id
    assert created_state["decision_type"] == "sentenca"
    assert created_state["decision_title"] == "Sentença parcialmente procedente"
    assert len(created_state["decision_points"]) == 2

    state_id = created_state["id"]

    r_list = client.get(
        f"/api/v1/appeal-reaction-states/case/{case_id}",
        headers=headers,
    )
    assert r_list.status_code == 200
    listed_states = r_list.json()
    assert any(state["id"] == state_id for state in listed_states)

    deadline_payload = {
        "key": "ro_deadline",
        "title": "Prazo para recurso ordinário",
        "due_date": "2026-03-28",
        "status": "pending",
        "metadata": {
            "calendar_source": "test",
        },
    }

    r_deadline = client.post(
        f"/api/v1/appeal-reaction-states/{state_id}/deadlines",
        json=deadline_payload,
        headers=headers,
    )
    assert r_deadline.status_code == 200
    deadline_detail = r_deadline.json()
    assert len(deadline_detail["deadlines"]) == 1
    assert deadline_detail["deadlines"][0]["deadline_key"] == "ro_deadline"

    strategy_payload = {
        "key": "attack_fgts_basis",
        "title": "Atacar fundamento do FGTS",
        "description": "Reforçar prova documental e atacar a valoração da prova sobre depósitos.",
        "target_point_keys": ["fgts_denied"],
        "priority": "high",
        "metadata": {
            "source": "test_strategy",
        },
    }

    r_strategy = client.post(
        f"/api/v1/appeal-reaction-states/{state_id}/strategy-items",
        json=strategy_payload,
        headers=headers,
    )
    assert r_strategy.status_code == 200
    strategy_detail = r_strategy.json()
    assert len(strategy_detail["strategy_items"]) == 1
    assert strategy_detail["strategy_items"][0]["strategy_key"] == "attack_fgts_basis"
    assert strategy_detail["strategy_items"][0]["target_point_keys"] == ["fgts_denied"]

    draft_payload = {
        "document_type": "recurso_ordinario",
        "title": "Minuta de recurso ordinário",
        "status": "draft",
        "version": 1,
        "metadata": {
            "source": "test_draft",
        },
    }

    r_draft = client.post(
        f"/api/v1/appeal-reaction-states/{state_id}/drafts",
        json=draft_payload,
        headers=headers,
    )
    assert r_draft.status_code == 200
    draft_detail = r_draft.json()
    assert len(draft_detail["appeal_drafts"]) == 1
    assert draft_detail["appeal_drafts"][0]["document_type"] == "recurso_ordinario"

    r_detail = client.get(
        f"/api/v1/appeal-reaction-states/{state_id}",
        headers=headers,
    )
    assert r_detail.status_code == 200
    detail = r_detail.json()

    assert detail["id"] == state_id
    assert len(detail["decision_points"]) == 2
    assert len(detail["deadlines"]) == 1
    assert len(detail["strategy_items"]) == 1
    assert len(detail["appeal_drafts"]) == 1

    r_summary = client.get(
        f"/api/v1/appeal-reaction-states/{state_id}/summary",
        headers=headers,
    )
    assert r_summary.status_code == 200
    summary = r_summary.json()

    assert summary["decision_type"] == "sentenca"
    assert summary["decision_title"] == "Sentença parcialmente procedente"
    assert len(summary["unfavorable_points"]) == 2
    assert summary["unfavorable_points"][0]["key"] in {"fgts_denied", "moral_damage_denied"}
    assert len(summary["deadlines"]) == 1
    assert summary["deadlines"][0]["key"] == "ro_deadline"
    assert len(summary["strategy_items"]) == 1
    assert summary["strategy_items"][0]["key"] == "attack_fgts_basis"
    assert summary["strategy_items"][0]["target_point_keys"] == ["fgts_denied"]
    assert len(summary["appeal_drafts"]) == 1
    assert summary["appeal_drafts"][0]["document_type"] == "recurso_ordinario"
