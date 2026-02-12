from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def login_admin():
    # cria admin (se não existir)
    client.post(
        "/api/v1/auth/seed-admin",
        headers={"x-seed-token": "CHANGE_ME_SEED_TOKEN"},
        json={"username": "admin_test", "password": "123456", "role": "admin"},
    )

    r = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "123456"},
    )
    return r.json()["access_token"]


def test_case_analysis_history_flow():
    token = login_admin()
    headers = {"Authorization": f"Bearer {token}"}

    # cria case
    r = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "case_number": f"TEST-{uuid.uuid4().hex[:8]}",
            "title": "Teste histórico",
            "description": "Teste",
            "status": "draft",
        },
    )
    assert r.status_code == 200
    case_id = r.json()["id"]

    # roda análise
    r = client.get(f"/api/v1/cases/{case_id}/analysis", headers=headers)
    assert r.status_code == 200

    # consulta histórico
    r = client.get(
        f"/api/v1/cases/{case_id}/analysis/history?limit=5",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["case_id"] == case_id
