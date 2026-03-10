from app.models.audit_log import AuditLog
from app.models.tenant import Tenant


def test_admin_audit_logs_requires_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    r = client.get("/api/v1/admin/audit/logs")
    assert r.status_code == 403


def test_admin_audit_logs_returns_logs_and_filters(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    tenant_a = Tenant(name="Tenant Audit A", plan="free")
    tenant_b = Tenant(name="Tenant Audit B", plan="free")
    db_session.add_all([tenant_a, tenant_b])
    db_session.commit()

    logs = [
        AuditLog(
            tenant_id=tenant_a.id,
            request_id="req-1",
            method="GET",
            path="/api/v1/cases",
            status_code=200,
            process_time_ms=12.5,
            username="userA@example.com",
            role="admin",
            client_ip="127.0.0.1",
            user_agent="pytest",
        ),
        AuditLog(
            tenant_id=tenant_a.id,
            request_id="req-2",
            method="POST",
            path="/api/v1/cases",
            status_code=201,
            process_time_ms=18.0,
            username="userA@example.com",
            role="admin",
            client_ip="127.0.0.1",
            user_agent="pytest",
        ),
        AuditLog(
            tenant_id=tenant_b.id,
            request_id="req-3",
            method="GET",
            path="/api/v1/admin/tenants",
            status_code=403,
            process_time_ms=9.0,
            username="userB@example.com",
            role="advogado",
            client_ip="127.0.0.1",
            user_agent="pytest",
        ),
    ]
    db_session.add_all(logs)
    db_session.commit()

    r = client.get(
        "/api/v1/admin/audit/logs",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r.status_code == 200

    data = r.json()
    assert data["count"] == 3
    assert len(data["items"]) == 3

    r2 = client.get(
        f"/api/v1/admin/audit/logs?tenant_id={tenant_a.id}&path=/api/v1/cases&limit=10",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r2.status_code == 200

    data2 = r2.json()
    assert data2["count"] == 2
    assert len(data2["items"]) == 2
    assert all(item["tenant_id"] == tenant_a.id for item in data2["items"])
    assert all(item["path"] == "/api/v1/cases" for item in data2["items"])

    r3 = client.get(
        "/api/v1/admin/audit/logs?status_code=403",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert r3.status_code == 200

    data3 = r3.json()
    assert data3["count"] == 1
    assert data3["items"][0]["status_code"] == 403
