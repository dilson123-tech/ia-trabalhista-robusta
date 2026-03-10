import uuid
from datetime import datetime, timezone

from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.core.security import pwd_context


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
    member = TenantMember(user_id=user_id, tenant_id=tenant_id, role="admin")
    db.add(member)


def create_subscription(db, tenant_id):
    sub = Subscription(
        tenant_id=tenant_id,
        plan_type="basic",
        status="active",
        case_limit=10,
        active=True,
        expires_at=datetime.now(timezone.utc),
    )
    db.add(sub)


def login(client, username, password):
    r = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_cross_tenant_isolation(client, db_session):
    tenant_a = create_tenant(db_session, f"TenantA_{uuid.uuid4()}")
    tenant_b = create_tenant(db_session, f"TenantB_{uuid.uuid4()}")

    create_subscription(db_session, tenant_a.id)
    create_subscription(db_session, tenant_b.id)
    db_session.commit()

    password = "123456"
    user_a = create_user(db_session, f"userA_{uuid.uuid4()}@example.com", password)
    user_b = create_user(db_session, f"userB_{uuid.uuid4()}@example.com", password)

    link_user_to_tenant(db_session, user_a.id, tenant_a.id)
    link_user_to_tenant(db_session, user_b.id, tenant_b.id)
    db_session.commit()

    token_a = login(client, user_a.username, password)
    token_b = login(client, user_b.username, password)

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
