from app.core.security import issue_token, pwd_context
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User


def test_cross_tenant_isolation(client, db_session):
    tenant_a = Tenant(name="Tenant A", plan="free")
    tenant_b = Tenant(name="Tenant B", plan="free")
    db_session.add_all([tenant_a, tenant_b])
    db_session.commit()

    user_a = User(
        username="userA@example.com",
        password_hash=pwd_context.hash("dev"),
        role="admin",
        is_active=True,
    )
    user_b = User(
        username="userB@example.com",
        password_hash=pwd_context.hash("dev"),
        role="admin",
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    db_session.add_all(
        [
            TenantMember(tenant_id=tenant_a.id, user_id=user_a.id, role="admin"),
            TenantMember(tenant_id=tenant_b.id, user_id=user_b.id, role="admin"),
        ]
    )
    db_session.commit()

    token_a = issue_token(user_a.username, "admin", tenant_a.id)
    token_b = issue_token(user_b.username, "admin", tenant_b.id)

    case_resp = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "case_number": "ISO-001",
            "title": "Caso Isolamento",
            "description": "Teste multi-tenant",
            "status": "ativo",
        },
    )
    assert case_resp.status_code == 200
    case_id = case_resp.json()["id"]

    forbidden_resp = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden_resp.status_code in (403, 404)
