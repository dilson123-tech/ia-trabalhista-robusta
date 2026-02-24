import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.session import SessionLocal
from app.core.security import issue_token

client = TestClient(app)


def test_cross_tenant_isolation():
    db = SessionLocal()

    # Criar tenants
    db.execute(text("INSERT INTO tenants (id, name) VALUES (100, 'Tenant A') ON CONFLICT DO NOTHING"))
    db.execute(text("INSERT INTO tenants (id, name) VALUES (200, 'Tenant B') ON CONFLICT DO NOTHING"))

    # Criar usuários
    db.execute(text("INSERT INTO users (username, password_hash, role) VALUES ('userA', 'fake', 'admin') ON CONFLICT DO NOTHING"))
    db.execute(text("INSERT INTO users (username, password_hash, role) VALUES ('userB', 'fake', 'admin') ON CONFLICT DO NOTHING"))

    # Buscar IDs
    userA_id = db.execute(text("SELECT id FROM users WHERE username='userA'")).fetchone()[0]
    userB_id = db.execute(text("SELECT id FROM users WHERE username='userB'")).fetchone()[0]

    # Criar membership
    db.execute(text("INSERT INTO tenant_members (tenant_id, user_id, role) VALUES (100, :uid, 'admin') ON CONFLICT DO NOTHING"), {"uid": userA_id})
    db.execute(text("INSERT INTO tenant_members (tenant_id, user_id, role) VALUES (200, :uid, 'admin') ON CONFLICT DO NOTHING"), {"uid": userB_id})

    db.commit()

    # Gerar tokens direto
    tokenA = issue_token("userA", "admin", 100)
    tokenB = issue_token("userB", "admin", 200)

    # Criar case no tenant A
    case_resp = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {tokenA}"},
        json={
            "case_number": "ISO-001",
            "title": "Caso Isolamento",
            "description": "Teste multi-tenant",
            "status": "ativo"
        }
    )
    assert case_resp.status_code == 200
    case_id = case_resp.json()["id"]

    # Tenant B tenta acessar
    forbidden_resp = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {tokenB}"}
    )

    assert forbidden_resp.status_code == 404

    db.close()
