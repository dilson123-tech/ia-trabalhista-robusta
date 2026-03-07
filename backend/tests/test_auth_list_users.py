from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User

# pega o mesmo hasher do auth real (não inventa outro)
from app.api.v1.routes.auth import pwd_context


def _seed_tenant_and_users(db):
    # Tenant 1
    t = db.query(Tenant).filter(Tenant.id == 1).first()
    if not t:
        t = Tenant(id=1, name="Tenant Teste 1")
        db.add(t)
        db.commit()

    # Admin
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=pwd_context.hash("dev"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    m = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == 1, TenantMember.user_id == admin.id)
        .first()
    )
    if not m:
        db.add(TenantMember(tenant_id=1, user_id=admin.id, role="admin"))
        db.commit()

    # Advogado (não-admin)
    adv = db.query(User).filter(User.username == "adv1").first()
    if not adv:
        adv = User(
            username="adv1",
            password_hash=pwd_context.hash("dev"),
            role="advogado",
            is_active=True,
        )
        db.add(adv)
        db.commit()
        db.refresh(adv)

    m2 = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == 1, TenantMember.user_id == adv.id)
        .first()
    )
    if not m2:
        db.add(TenantMember(tenant_id=1, user_id=adv.id, role="advogado"))
        db.commit()

    return admin, adv


def test_list_users_admin_only(client, db_session):
    _seed_tenant_and_users(db_session)

    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "dev"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    assert any(u.get("username") == "admin" for u in data)


def test_list_users_forbidden_for_non_admin(client, db_session):
    _seed_tenant_and_users(db_session)

    r = client.post("/api/v1/auth/login", json={"username": "adv1", "password": "dev"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
