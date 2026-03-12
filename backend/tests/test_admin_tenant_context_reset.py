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


def create_user(db, username, password, role="admin"):
    user = User(
        username=username,
        password_hash=pwd_context.hash(password),
        role=role,
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
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def ensure_subscription(db, tenant_id):
    set_tenant_on_session(db, tenant_id)
    db.execute(
        text(
            "INSERT INTO subscriptions (tenant_id, plan_type, status, case_limit, active, expires_at) "
            "VALUES (:tid, 'basic', 'active', 10, TRUE, NOW() + INTERVAL '1 year') "
            "ON CONFLICT (tenant_id) DO NOTHING"
        ),
        {"tid": tenant_id},
    )


def test_admin_request_does_not_leak_tenant_context(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "pytest-admin-key")

    db = SessionLocal()

    tenant_a = create_tenant(db, f"TenantA_{uuid.uuid4()}")
    tenant_b = create_tenant(db, f"TenantB_{uuid.uuid4()}")

    ensure_subscription(db, tenant_a.id)
    ensure_subscription(db, tenant_b.id)

    password = "123456"
    user_a = create_user(db, f"userA_{uuid.uuid4()}@example.com", password, role="admin")
    user_b = create_user(db, f"userB_{uuid.uuid4()}@example.com", password, role="admin")

    link_user_to_tenant(db, user_a.id, tenant_a.id)
    link_user_to_tenant(db, user_b.id, tenant_b.id)
    db.commit()

    username_a = user_a.username
    db.close()

    token_a = login(username_a, password)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    r_create = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"A-{uuid.uuid4().hex[:8]}",
            "title": "Caso Tenant A",
            "description": "Caso visível apenas para tenant A",
            "status": "draft",
        },
        headers=headers_a,
    )
    assert r_create.status_code == 200
    case_a_id = r_create.json()["id"]

    admin_headers = {
        "X-Admin-Key": "pytest-admin-key",
        "X-Admin-Actor": "pytest-admin-context-reset",
    }

    r_admin = client.get(
        f"/api/v1/admin/tenants/{tenant_b.id}/usage/summary",
        headers=admin_headers,
    )
    assert r_admin.status_code == 200
    assert r_admin.json()["tenant_id"] == tenant_b.id

    r_list = client.get("/api/v1/cases", headers=headers_a)
    assert r_list.status_code == 200

    items = r_list.json()
    ids = [item["id"] for item in items]

    assert case_a_id in ids
    assert len(items) == 1
