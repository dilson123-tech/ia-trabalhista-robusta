from datetime import datetime, timezone, date

from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.usage_counter import UsageCounter
from app.models.user import User
from app.core.security import pwd_context


def test_admin_tenant_usage_full_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get("/api/v1/admin/tenants/1/usage/full")
    assert r.status_code == 403


def test_admin_tenant_usage_full_returns_consolidated_view(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant = Tenant(name="Tenant Full View", plan="free")
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

    user1 = User(
        username="full1@example.com",
        password_hash=pwd_context.hash("dev"),
        role="admin",
        is_active=True,
    )
    user2 = User(
        username="full2@example.com",
        password_hash=pwd_context.hash("dev"),
        role="advogado",
        is_active=False,
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    db_session.add_all(
        [
            TenantMember(tenant_id=tenant.id, user_id=user1.id, role="owner"),
            TenantMember(tenant_id=tenant.id, user_id=user2.id, role="advogado"),
        ]
    )

    month = date.today().replace(day=1)
    counter = UsageCounter(
        tenant_id=tenant.id,
        month=month,
        cases_created=7,
        ai_analyses_generated=3,
    )
    db_session.add(counter)
    db_session.commit()

    r = client.get(
        f"/api/v1/admin/tenants/{tenant.id}/usage/full",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["tenant"]["tenant_id"] == tenant.id
    assert data["tenant"]["name"] == "Tenant Full View"

    assert data["subscription"]["plan_type"] == "pro"
    assert data["subscription"]["status"] == "active"
    assert data["subscription"]["active"] is True
    assert data["subscription"]["case_limit"] == 50

    assert data["users"]["count"] == 2
    usernames = [item["username"] for item in data["users"]["items"]]
    assert "full1@example.com" in usernames
    assert "full2@example.com" in usernames

    assert data["usage_summary"]["used"]["cases_created"] == 7
    assert data["usage_summary"]["used"]["ai_analyses_generated"] == 3
    assert data["usage_summary"]["limits"]["cases_per_month"] == 50
    assert data["usage_summary"]["remaining"]["cases"] == 43


def test_admin_tenant_usage_full_returns_404_for_missing_tenant(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get(
        "/api/v1/admin/tenants/999/usage/full",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 404
