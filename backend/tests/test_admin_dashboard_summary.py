from datetime import datetime, timezone

from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import pwd_context


def test_admin_dashboard_summary_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get("/api/v1/admin/dashboard/summary")
    assert r.status_code == 403


def test_admin_dashboard_summary_returns_global_counts(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenants = [
        Tenant(name="Tenant A", plan="free"),
        Tenant(name="Tenant B", plan="free"),
        Tenant(name="Tenant C", plan="free"),
    ]
    db_session.add_all(tenants)
    db_session.commit()

    users = [
        User(username="u1@example.com", password_hash=pwd_context.hash("dev"), role="admin", is_active=True),
        User(username="u2@example.com", password_hash=pwd_context.hash("dev"), role="advogado", is_active=True),
        User(username="u3@example.com", password_hash=pwd_context.hash("dev"), role="admin", is_active=False),
    ]
    db_session.add_all(users)
    db_session.commit()

    subs = [
        Subscription(
            tenant_id=tenants[0].id,
            plan_type="basic",
            status="active",
            case_limit=10,
            active=True,
            expires_at=datetime.now(timezone.utc),
        ),
        Subscription(
            tenant_id=tenants[1].id,
            plan_type="pro",
            status="trial",
            case_limit=50,
            active=True,
            expires_at=datetime.now(timezone.utc),
        ),
        Subscription(
            tenant_id=tenants[2].id,
            plan_type="office",
            status="canceled",
            case_limit=200,
            active=False,
            expires_at=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(subs)
    db_session.commit()

    r = client.get(
        "/api/v1/admin/dashboard/summary",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["tenants_total"] == 3
    assert data["users_total"] == 3
    assert data["subscriptions_total"] == 3
    assert data["subscriptions_active"] == 1
    assert data["subscriptions_trial"] == 1
    assert data["subscriptions_canceled"] == 1
    assert data["subscriptions_active_flag_true"] == 2
    assert data["subscriptions_active_flag_false"] == 1

    assert data["subscriptions_by_plan"]["basic"] == 1
    assert data["subscriptions_by_plan"]["pro"] == 1
    assert data["subscriptions_by_plan"]["office"] == 1
