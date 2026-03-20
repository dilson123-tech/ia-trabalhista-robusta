from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_succ_{uuid.uuid4().hex[:8]}@example.com",
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


def test_case_party_state_authenticated_succession_flow(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"SUCC-{uuid.uuid4().hex[:8]}",
        "title": "Caso de teste de sucessão processual",
        "description": "Validação da persistência/API de partes, histórico e sucessão.",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_state_payload = {
        "case_id": case_id,
        "area": "trabalhista",
        "parties": [
            {
                "key": "claimant_1",
                "name": "Carlos Pereira",
                "role": "reclamante",
                "party_type": "person",
                "document_id": "222.222.222-22",
                "status": "active",
                "is_original_party": True,
                "metadata": {
                    "party_key": "claimant_1",
                    "party_type": "person",
                },
            },
            {
                "key": "respondent_1",
                "name": "Metalúrgica Beta",
                "role": "reclamada",
                "party_type": "company",
                "document_id": "98.765.432/0001-10",
                "status": "active",
                "is_original_party": True,
                "metadata": {
                    "party_key": "respondent_1",
                    "party_type": "company",
                },
            },
        ],
        "metadata": {
            "source": "test_case_party_states_flow",
        },
    }

    r_create_state = client.post(
        "/api/v1/case-party-states",
        json=create_state_payload,
        headers=headers,
    )
    assert r_create_state.status_code == 200
    created_state = r_create_state.json()

    assert created_state["case_id"] == case_id
    assert created_state["area"] == "trabalhista"
    assert len(created_state["parties"]) == 2
    assert created_state["events"][0]["event_type"] == "initial_party_state_created"

    state_id = created_state["id"]

    r_list = client.get(
        f"/api/v1/case-party-states/case/{case_id}",
        headers=headers,
    )
    assert r_list.status_code == 200
    listed_states = r_list.json()
    assert any(state["id"] == state_id for state in listed_states)

    succession_payload = {
        "original_party_key": "claimant_1",
        "successor_party": {
            "key": "claimant_successor_1",
            "name": "Ana Pereira",
            "role": "reclamante",
            "party_type": "person",
            "document_id": "333.333.333-33",
            "status": "active",
            "is_original_party": False,
            "metadata": {
                "qualification": "herdeira sucessora",
            },
        },
        "relationship_type": "procedural_successor",
        "occurred_on": "2026-03-20",
        "description": "Falecimento da parte originária com habilitação de sucessora.",
    }

    r_succession = client.post(
        f"/api/v1/case-party-states/{state_id}/succession",
        json=succession_payload,
        headers=headers,
    )
    assert r_succession.status_code == 200
    succession_detail = r_succession.json()

    assert len(succession_detail["parties"]) == 3
    assert len(succession_detail["relationships"]) == 1
    assert succession_detail["events"][-1]["event_type"] == "succession_registered"

    original_party = next(
        party for party in succession_detail["parties"] if party["party_key"] == "claimant_1"
    )
    successor_party = next(
        party
        for party in succession_detail["parties"]
        if party["party_key"] == "claimant_successor_1"
    )
    relationship = succession_detail["relationships"][0]

    assert original_party["status"] == "succeeded"
    assert original_party["party_metadata"]["succession_preserved"] is True
    assert original_party["party_metadata"]["successor_party_key"] == "claimant_successor_1"

    assert successor_party["is_original_party"] is False
    assert successor_party["party_metadata"]["origin_party_key"] == "claimant_1"

    assert relationship["relationship_type"] == "procedural_successor"
    assert relationship["source_party_key"] == "claimant_1"
    assert relationship["target_party_key"] == "claimant_successor_1"

    r_detail = client.get(
        f"/api/v1/case-party-states/{state_id}",
        headers=headers,
    )
    assert r_detail.status_code == 200
    detail = r_detail.json()

    original_party_detail = next(
        party for party in detail["parties"] if party["party_key"] == "claimant_1"
    )
    assert original_party_detail["party_metadata"]["succession_preserved"] is True
    assert original_party_detail["party_metadata"]["successor_party_key"] == "claimant_successor_1"

    r_snapshot = client.get(
        f"/api/v1/case-party-states/{state_id}/snapshot",
        headers=headers,
    )
    assert r_snapshot.status_code == 200
    snapshot = r_snapshot.json()

    active_keys = [party["party_key"] for party in snapshot["active_parties"]]
    historical_keys = [party["party_key"] for party in snapshot["historical_parties"]]

    assert "claimant_successor_1" in active_keys
    assert "respondent_1" in active_keys
    assert "claimant_1" in historical_keys
    assert len(snapshot["succession_relationships"]) == 1
    assert snapshot["succession_relationships"][0]["target_party_key"] == "claimant_successor_1"
