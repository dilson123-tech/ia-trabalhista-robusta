from datetime import datetime, timezone

from app.models.tenant import Tenant
from app.models.subscription import Subscription


def test_admin_toggle_subscription_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.patch(
        "/api/v1/admin/tenants/1/subscription/active",
        json={"active": False},
    )
    assert r.status_code == 403


def test_admin_toggle_subscription_deactivates_subscription(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant = Tenant(name="Tenant Toggle", plan="free")
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

    r = client.patch(
        f"/api/v1/admin/tenants/{tenant.id}/subscription/active",
        json={"active": False},
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["tenant_id"] == tenant.id
    assert data["subscription"]["active"] is False
    assert data["subscription"]["status"] == "canceled"
    assert data["subscription"]["plan_type"] == "pro"


def test_admin_toggle_subscription_reactivates_subscription(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant = Tenant(name="Tenant Reactivate", plan="free")
    db_session.add(tenant)
    db_session.commit()

    sub = Subscription(
        tenant_id=tenant.id,
        plan_type="basic",
        status="canceled",
        case_limit=10,
        active=False,
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(sub)
    db_session.commit()

    r = client.patch(
        f"/api/v1/admin/tenants/{tenant.id}/subscription/active",
        json={"active": True},
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["tenant_id"] == tenant.id
    assert data["subscription"]["active"] is True
    assert data["subscription"]["status"] == "active"
    assert data["subscription"]["plan_type"] == "basic"


def test_admin_toggle_subscription_returns_404_when_subscription_missing(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant = Tenant(name="Tenant Without Subscription", plan="free")
    db_session.add(tenant)
    db_session.commit()

    r = client.patch(
        f"/api/v1/admin/tenants/{tenant.id}/subscription/active",
        json={"active": False},
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 404
