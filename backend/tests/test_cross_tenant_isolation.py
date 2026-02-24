from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cross_tenant_isolation():
    # Login admin2 (tenant 183)
    r = client.post("/api/v1/auth/login", json={
        "username": "admin2",
        "password": "123456"
    })
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Deve listar apenas casos do próprio tenant
    r = client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200

    # Tentar acessar caso de outro tenant (ID fixo conhecido)
    r = client.get(
        "/api/v1/cases/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Não pode retornar o caso
    assert r.status_code in (403, 404)
