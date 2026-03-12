from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.api.v1.routes.auth import pwd_context


def _seed_admin_and_target_user(db):
    tenant = db.query(Tenant).filter(Tenant.id == 1).first()
    if not tenant:
        tenant = Tenant(id=1, name="Tenant Teste 1")
        db.add(tenant)
        db.commit()

    admin = db.query(User).filter(User.username == "admin_revoke").first()
    if not admin:
        admin = User(
            username="admin_revoke",
            password_hash=pwd_context.hash("dev"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    admin_membership = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == 1, TenantMember.user_id == admin.id)
        .first()
    )
    if not admin_membership:
        db.add(TenantMember(tenant_id=1, user_id=admin.id, role="admin"))
        db.commit()

    target = db.query(User).filter(User.username == "adv_revoke").first()
    if not target:
        target = User(
            username="adv_revoke",
            password_hash=pwd_context.hash("dev"),
            role="advogado",
            is_active=True,
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    target_membership = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == 1, TenantMember.user_id == target.id)
        .first()
    )
    if not target_membership:
        db.add(TenantMember(tenant_id=1, user_id=target.id, role="advogado"))
        db.commit()

    return admin, target


def test_token_stops_working_after_user_deactivation(client, db_session):
    admin, target = _seed_admin_and_target_user(db_session)

    login_admin = client.post(
        "/api/v1/auth/login",
        json={"username": admin.username, "password": "dev"},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]

    login_target = client.post(
        "/api/v1/auth/login",
        json={"username": target.username, "password": "dev"},
    )
    assert login_target.status_code == 200
    target_token = login_target.json()["access_token"]

    before = client.get(
        "/api/v1/auth/whoami",
        headers={"Authorization": f"Bearer {target_token}"},
    )
    assert before.status_code == 200
    assert before.json()["username"] == target.username

    deactivate = client.patch(
        f"/api/v1/auth/users/{target.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    after = client.get(
        "/api/v1/auth/whoami",
        headers={"Authorization": f"Bearer {target_token}"},
    )
    assert after.status_code == 403
    assert "inactive" in after.json()["detail"].lower()
