import uuid

from app.core.settings import settings
from app.api.v1.routes import cases as cases_routes


def _auth_headers(client, monkeypatch):
    def _skip_plan_limits(*args, **kwargs):
        return None

    monkeypatch.setattr(cases_routes, "enforce_plan_limits", _skip_plan_limits)
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_timeline_{uuid.uuid4().hex[:8]}@example.com",
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


def test_case_timeline_authenticated_flow(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)

    r_case = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"TIMELINE-{uuid.uuid4().hex[:8]}",
            "title": "Caso de teste da linha do tempo",
            "description": "Validação de linha do tempo estruturada por caso.",
            "legal_area": "civel",
            "action_type": "caso novo / inicial / validação do sistema",
            "status": "draft",
        },
        headers=headers,
    )
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    r_create = client.post(
        f"/api/v1/cases/{case_id}/timeline",
        json={
            "event_date": "2019/2020",
            "title": "Formação da relação de locação",
            "description": "Discussão inicial sobre a locação da carreta/semi-reboque.",
            "related_evidence": "Petição inicial original e roteiro de audiência.",
            "related_witness": "Rosangela de Lourdes Siqueira",
            "pending_note": "Localizar contrato de locação completo.",
            "sort_order": 1,
            "metadata": {
                "source": "case_timeline_v1",
            },
        },
        headers=headers,
    )
    assert r_create.status_code == 200
    created = r_create.json()
    assert created["case_id"] == case_id
    assert created["event_date"] == "2019/2020"
    assert created["title"] == "Formação da relação de locação"
    assert created["sort_order"] == 1
    assert created["timeline_metadata"]["source"] == "case_timeline_v1"

    item_id = created["id"]

    r_list = client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert r_list.status_code == 200
    items = r_list.json()
    assert len(items) == 1
    assert items[0]["id"] == item_id

    r_update = client.patch(
        f"/api/v1/cases/{case_id}/timeline/{item_id}",
        json={
            "event_date": "2019",
            "title": "Locação e uso do semi-reboque",
            "description": "Fato ajustado para detalhar locação, uso e pendência documental.",
            "related_evidence": "Petição inicial original do processo-base.",
            "related_witness": "Edson Estevão",
            "pending_note": "Conferir BO e contrato.",
            "sort_order": 2,
            "metadata": {
                "updated_by": "test",
            },
        },
        headers=headers,
    )
    assert r_update.status_code == 200
    updated = r_update.json()
    assert updated["event_date"] == "2019"
    assert updated["title"] == "Locação e uso do semi-reboque"
    assert updated["related_witness"] == "Edson Estevão"
    assert updated["sort_order"] == 2
    assert updated["timeline_metadata"]["source"] == "case_timeline_v1"
    assert updated["timeline_metadata"]["updated_by"] == "test"

    r_delete = client.delete(
        f"/api/v1/cases/{case_id}/timeline/{item_id}",
        headers=headers,
    )
    assert r_delete.status_code == 204

    r_list_after_delete = client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert r_list_after_delete.status_code == 200
    assert r_list_after_delete.json() == []


def test_case_timeline_rejects_missing_required_fields(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)

    r_case = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"TIMELINE-BAD-{uuid.uuid4().hex[:8]}",
            "title": "Caso para timeline inválida",
            "description": "Validação de campos obrigatórios da timeline.",
            "legal_area": "civel",
            "action_type": "caso novo",
            "status": "draft",
        },
        headers=headers,
    )
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    r_bad = client.post(
        f"/api/v1/cases/{case_id}/timeline",
        json={
            "event_date": "2026",
            "title": "",
            "description": "",
        },
        headers=headers,
    )
    assert r_bad.status_code == 422
