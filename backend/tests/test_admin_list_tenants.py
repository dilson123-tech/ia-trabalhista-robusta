import os
from datetime import datetime, timezone

from app.models.tenant import Tenant
from app.models.subscription import Subscription


def test_admin_list_tenants_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    r = client.get("/api/v1/admin/tenants")
    assert r.status_code == 403


def test_admin_list_tenants_returns_items_and_filters(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    t1 = Tenant(name="Escritorio Alpha", plan="free")
    t2 = Tenant(name="Beta Juridico", plan="free")
    db_session.add_all([t1, t2])
    db_session.commit()

    s1 = Subscription(
        tenant_id=t1.id,
        plan_type="basic",
        status="trial",
        case_limit=10,
        active=True,
        expires_at=datetime.now(timezone.utc),
    )
    s2 = Subscription(
        tenant_id=t2.id,
        plan_type="pro",
        status="active",
        case_limit=50,
        active=True,
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    r = client.get(
        "/api/v1/admin/tenants",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    names = [item["name"] for item in data["items"]]
    assert "Escritorio Alpha" in names
    assert "Beta Juridico" in names

    r2 = client.get(
        "/api/v1/admin/tenants?plan_type=pro&status=active",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["total"] == 1
    assert len(data2["items"]) == 1
    assert data2["items"][0]["name"] == "Beta Juridico"


def test_admin_list_tenants_filters_by_name(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    t1 = Tenant(name="Gamma Legal", plan="free")
    t2 = Tenant(name="Delta Office", plan="free")
    db_session.add_all([t1, t2])
    db_session.commit()

    db_session.add_all(
        [
            Subscription(
                tenant_id=t1.id,
                plan_type="basic",
                status="trial",
                case_limit=10,
                active=True,
                expires_at=datetime.now(timezone.utc),
            ),
            Subscription(
                tenant_id=t2.id,
                plan_type="office",
                status="active",
                case_limit=200,
                active=True,
                expires_at=datetime.now(timezone.utc),
            ),
        ]
    )
    db_session.commit()

    r = client.get(
        "/api/v1/admin/tenants?name=gamma",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Gamma Legal"
