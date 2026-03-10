from datetime import datetime, timezone

from app.models.tenant import Tenant
from app.models.subscription import Subscription


def test_admin_get_subscription_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get("/api/v1/admin/tenants/1/subscription")
    assert r.status_code == 403


def test_admin_get_subscription_returns_subscription_data(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant = Tenant(name="Tenant Subscription", plan="free")
    db_session.add(tenant)
    db_session.commit()

    sub = Subscription(
        tenant_id=tenant.id,
        plan_type="pro",
        status="active",
        case_limit=50,
        active=True,
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(sub)
    db_session.commit()

    r = client.get(
        f"/api/v1/admin/tenants/{tenant.id}/subscription",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["tenant_id"] == tenant.id
    assert data["subscription"]["plan_type"] == "pro"
    assert data["subscription"]["status"] == "active"
    assert data["subscription"]["active"] is True
    assert data["subscription"]["case_limit"] == 50
    assert data["subscription"]["expires_at"] is not None


def test_admin_get_subscription_returns_404_when_missing(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant = Tenant(name="Tenant No Subscription", plan="free")
    db_session.add(tenant)
    db_session.commit()

    r = client.get(
        f"/api/v1/admin/tenants/{tenant.id}/subscription",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 404
