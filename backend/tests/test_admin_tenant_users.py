from app.models.tenant import Tenant
from app.models.user import User
from app.models.tenant_member import TenantMember
from app.core.security import pwd_context


def test_admin_tenant_users_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get("/api/v1/admin/tenants/1/users")
    assert r.status_code == 403


def test_admin_tenant_users_returns_only_users_from_target_tenant(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant_a = Tenant(name="Tenant Alpha", plan="free")
    tenant_b = Tenant(name="Tenant Beta", plan="free")
    db_session.add_all([tenant_a, tenant_b])
    db_session.commit()

    user_a1 = User(
        username="alpha1@example.com",
        password_hash=pwd_context.hash("dev"),
        role="admin",
        is_active=True,
    )
    user_a2 = User(
        username="alpha2@example.com",
        password_hash=pwd_context.hash("dev"),
        role="advogado",
        is_active=False,
    )
    user_b1 = User(
        username="beta1@example.com",
        password_hash=pwd_context.hash("dev"),
        role="admin",
        is_active=True,
    )
    db_session.add_all([user_a1, user_a2, user_b1])
    db_session.commit()

    db_session.add_all(
        [
            TenantMember(tenant_id=tenant_a.id, user_id=user_a1.id, role="owner"),
            TenantMember(tenant_id=tenant_a.id, user_id=user_a2.id, role="advogado"),
            TenantMember(tenant_id=tenant_b.id, user_id=user_b1.id, role="owner"),
        ]
    )
    db_session.commit()

    r = client.get(
        f"/api/v1/admin/tenants/{tenant_a.id}/users",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["tenant_id"] == tenant_a.id
    assert data["count"] == 2
    assert len(data["items"]) == 2

    usernames = [item["username"] for item in data["items"]]
    assert "alpha1@example.com" in usernames
    assert "alpha2@example.com" in usernames
    assert "beta1@example.com" not in usernames

    by_username = {item["username"]: item for item in data["items"]}
    assert by_username["alpha1@example.com"]["tenant_role"] == "owner"
    assert by_username["alpha1@example.com"]["is_active"] is True
    assert by_username["alpha2@example.com"]["tenant_role"] == "advogado"
    assert by_username["alpha2@example.com"]["is_active"] is False


def test_admin_tenant_users_returns_404_for_missing_tenant(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get(
        "/api/v1/admin/tenants/999/users",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 404
