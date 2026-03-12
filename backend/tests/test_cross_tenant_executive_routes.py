import uuid
from datetime import datetime, timezone

from app.core.security import pwd_context
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User


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
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def link_user_to_tenant(db, user_id, tenant_id):
    db.add(TenantMember(user_id=user_id, tenant_id=tenant_id, role="admin"))


def create_subscription(db, tenant_id):
    db.add(
        Subscription(
            tenant_id=tenant_id,
            plan_type="basic",
            status="active",
            case_limit=10,
            active=True,
            expires_at=datetime.now(timezone.utc),
        )
    )


def login(client, username, password):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_cross_tenant_access_blocked_on_executive_and_report_routes(client, db_session):
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

    create_case = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"A-{uuid.uuid4()}",
            "title": "Caso A",
            "description": "Desc A",
            "status": "draft",
        },
        headers=headers_a,
    )
    assert create_case.status_code == 200
    case_a_id = create_case.json()["id"]

    analyze = client.get(f"/api/v1/cases/{case_a_id}/analysis", headers=headers_a)
    assert analyze.status_code == 200

    routes = [
        f"/api/v1/cases/{case_a_id}/report",
        f"/api/v1/cases/{case_a_id}/executive-summary",
        f"/api/v1/cases/{case_a_id}/executive-report",
        f"/api/v1/cases/{case_a_id}/executive-pdf",
    ]

    for route in routes:
        response = client.get(route, headers=headers_b)
        assert response.status_code == 404, f"{route} should be isolated across tenants"
