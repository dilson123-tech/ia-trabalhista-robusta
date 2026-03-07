import uuid
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.tenant_member import TenantMember
from app.core.security import pwd_context
from app.core.tenant import set_tenant_on_session

client = TestClient(app)


def create_tenant(db, name):
    tenant = Tenant(name=name)
    db.add(tenant)
    db.flush()
    db.refresh(tenant)
    return tenant


def create_user(db, username, password):
    user = User(
        username=username,
        password_hash=pwd_context.hash(password),
        role="admin"
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def link_user_to_tenant(db, user_id, tenant_id):

    member = TenantMember(user_id=user_id, tenant_id=tenant_id)
    db.add(member)


def login(username, password):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_e2e_multi_tenant_isolation():
    db = SessionLocal()

    # Criar tenants
    tenant_a = create_tenant(db, f"TenantA_{uuid.uuid4()}")
    tenant_b = create_tenant(db, f"TenantB_{uuid.uuid4()}")
    set_tenant_on_session(db, tenant_a.id)
    db.execute(text("INSERT INTO subscriptions (tenant_id, plan_type, status, case_limit, active, expires_at) VALUES (:tid, 'basic', 'active', 10, TRUE, NOW() + INTERVAL '1 year')"), {"tid": tenant_a.id})

    set_tenant_on_session(db, tenant_b.id)
    db.execute(text("INSERT INTO subscriptions (tenant_id, plan_type, status, case_limit, active, expires_at) VALUES (:tid, 'basic', 'active', 10, TRUE, NOW() + INTERVAL '1 year')"), {"tid": tenant_b.id})
    db.commit()


    # Criar usuários
    password = "123456"
    user_a = create_user(db, f"userA_{uuid.uuid4()}", password)
    user_b = create_user(db, f"userB_{uuid.uuid4()}", password)

    # Vincular usuários
    link_user_to_tenant(db, user_a.id, tenant_a.id)

    link_user_to_tenant(db, user_b.id, tenant_b.id)
    db.commit()



    username_a = user_a.username
    username_b = user_b.username
    db.close()

    # Login
    token_a = login(username_a, password)
    token_b = login(username_b, password)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Criar caso A
    resp_a = client.post(
        "/api/v1/cases",
        json={
            "case_number": "A-001",
            "title": "Caso A",
            "description": "Desc A",
            "status": "draft"
        },
        headers=headers_a
    )
    assert resp_a.status_code == 200
    case_a_id = resp_a.json()["id"]

    # Criar caso B
    resp_b = client.post(
        "/api/v1/cases",
        json={
            "case_number": "B-001",
            "title": "Caso B",
            "description": "Desc B",
            "status": "draft"
        },
        headers=headers_b
    )
    assert resp_b.status_code == 200
    case_b_id = resp_b.json()["id"]

    # Tenant A lista casos
    list_a = client.get("/api/v1/cases", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    # Tenant B lista casos
    list_b = client.get("/api/v1/cases", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 1

    # Tenant A tenta acessar caso de B
    cross = client.get(f"/api/v1/cases/{case_b_id}", headers=headers_a)
    assert cross.status_code == 404


