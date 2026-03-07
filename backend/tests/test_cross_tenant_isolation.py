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
        role="admin",
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def link_user_to_tenant(db, user_id, tenant_id):
    member = TenantMember(user_id=user_id, tenant_id=tenant_id)
    db.add(member)


def create_subscription(db, tenant_id):
    set_tenant_on_session(db, tenant_id)
    db.execute(
        text(
            "INSERT INTO subscriptions "
            "(tenant_id, plan_type, status, case_limit, active, expires_at) "
            "VALUES (:tid, 'basic', 'active', 10, TRUE, NOW() + INTERVAL '1 year')"
        ),
        {"tid": tenant_id},
    )


def login(username, password):
    r = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_cross_tenant_isolation():
    db = SessionLocal()

    tenant_a = create_tenant(db, f"TenantA_{uuid.uuid4()}")
    tenant_b = create_tenant(db, f"TenantB_{uuid.uuid4()}")

    create_subscription(db, tenant_a.id)
    create_subscription(db, tenant_b.id)
    db.commit()

    password = "123456"
    user_a = create_user(db, f"userA_{uuid.uuid4()}", password)
    user_b = create_user(db, f"userB_{uuid.uuid4()}", password)

    link_user_to_tenant(db, user_a.id, tenant_a.id)
    link_user_to_tenant(db, user_b.id, tenant_b.id)
    db.commit()

    username_a = user_a.username
    username_b = user_b.username
    db.close()

    token_a = login(username_a, password)
    token_b = login(username_b, password)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp_a = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"A-{uuid.uuid4()}",
            "title": "Caso A",
            "description": "Desc A",
            "status": "draft",
        },
        headers=headers_a,
    )
    assert resp_a.status_code == 200
    case_a_id = resp_a.json()["id"]

    list_a = client.get("/api/v1/cases", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    cross = client.get(f"/api/v1/cases/{case_a_id}", headers=headers_b)
    assert cross.status_code in (403, 404)
