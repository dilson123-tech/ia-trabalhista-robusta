import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.plans import PlanType, limits_for
from app.core.settings import settings
from app.core.tenant import set_tenant_on_session
from app.db import session as db_session_module
from app.db.session import AdminDatabaseNotConfigured
from app.main import app
from app.models.billing_request import BillingRequest
from app.models.subscription import Subscription
from app.models.tenant import Tenant

# Webhook Asaas sob RLS (BLOCO 2): descoberta do tenant pela role admin,
# mutação pela role runtime com app.tenant_id aplicado. PG efêmero de teste.
pytestmark = pytest.mark.pg

WEBHOOK_TOKEN = "pytest-asaas-webhook-token"

client = TestClient(app)


@pytest.fixture(autouse=True)
def _webhook_token(monkeypatch):
    monkeypatch.setattr(settings, "ASAAS_WEBHOOK_TOKEN", WEBHOOK_TOKEN)


def create_tenant(db, name):
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_billing(db, tenant_id, plan="pro", status="checkout_pending"):
    set_tenant_on_session(db, tenant_id)
    billing = BillingRequest(
        tenant_id=tenant_id,
        requested_plan_type=plan,
        current_plan_type="basic",
        amount_cents=9900,
        status=status,
    )
    db.add(billing)
    db.commit()
    db.refresh(billing)
    return billing


def create_subscription(db, tenant_id, plan="basic", status="trial"):
    set_tenant_on_session(db, tenant_id)
    sub = Subscription(tenant_id=tenant_id, plan_type=plan, status=status, case_limit=10, active=True)
    db.add(sub)
    db.commit()
    return sub


def post_webhook(billing_id, event_name="PAYMENT_CONFIRMED", status="CONFIRMED", payment_id="pay_123"):
    return client.post(
        "/api/v1/webhooks/asaas",
        headers={"asaas-access-token": WEBHOOK_TOKEN},
        json={
            "event": event_name,
            "payment": {"id": payment_id, "status": status, "externalReference": str(billing_id)},
        },
    )


def admin_read(admin_factory, model, **filters):
    # Leitura global de verificação (role admin: somente SELECT).
    db = admin_factory()
    try:
        return db.query(model).filter_by(**filters).all()
    finally:
        db.close()


def seed_two_tenants(pg_request_db):
    db = pg_request_db()
    try:
        tenant_a = create_tenant(db, f"TenantA_{uuid.uuid4()}")
        tenant_b = create_tenant(db, f"TenantB_{uuid.uuid4()}")
        billing_a = create_billing(db, tenant_a.id, plan="pro")
        billing_b = create_billing(db, tenant_b.id, plan="office")
        create_subscription(db, tenant_b.id, plan="basic", status="trial")
        return tenant_a.id, tenant_b.id, billing_a.id, billing_b.id
    finally:
        db.close()


def test_payment_confirmed_activates_subscription_of_billing_tenant(pg_request_db, pg_admin_request_db):
    tenant_a, tenant_b, billing_a, billing_b = seed_two_tenants(pg_request_db)

    response = post_webhook(billing_a, payment_id="pay_a")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "ok": True,
        "billing_request_id": billing_a,
        "tenant_id": tenant_a,
        "plan_type": "pro",
        "provider_reference": "pay_a",
    }

    [billing] = admin_read(pg_admin_request_db, BillingRequest, id=billing_a)
    assert billing.status == "paid"
    assert billing.paid_at is not None
    assert billing.provider_reference == "pay_a"

    [sub] = admin_read(pg_admin_request_db, Subscription, tenant_id=tenant_a)
    assert sub.status == "active"
    assert sub.plan_type == "pro"
    assert sub.active is True
    assert sub.case_limit == limits_for(PlanType.pro).cases_per_month
    assert sub.expires_at is not None

    # Idempotência: reenvio do mesmo evento não reprocessa.
    again = post_webhook(billing_a, payment_id="pay_a")
    assert again.status_code == 200
    assert again.json() == {"ok": True, "already_paid": billing_a, "provider_reference": "pay_a"}


def test_payment_confirmed_updates_existing_subscription(pg_request_db, pg_admin_request_db):
    tenant_a, tenant_b, billing_a, billing_b = seed_two_tenants(pg_request_db)

    response = post_webhook(billing_b, payment_id="pay_b")
    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == tenant_b

    subs_b = admin_read(pg_admin_request_db, Subscription, tenant_id=tenant_b)
    assert len(subs_b) == 1
    assert subs_b[0].status == "active"
    assert subs_b[0].plan_type == "office"
    assert subs_b[0].case_limit == limits_for(PlanType.office).cases_per_month


def test_missing_billing_request_keeps_contract(pg_request_db, pg_admin_request_db):
    tenant_a, tenant_b, billing_a, billing_b = seed_two_tenants(pg_request_db)
    missing_id = max(billing_a, billing_b) + 1000

    response = post_webhook(missing_id)
    assert response.status_code == 200
    assert response.json() == {"ok": True, "missing_billing_request": missing_id}

    billings = admin_read(pg_admin_request_db, BillingRequest)
    assert {b.status for b in billings} == {"checkout_pending"}
    assert admin_read(pg_admin_request_db, Subscription, tenant_id=tenant_a) == []


def test_webhook_does_not_read_or_write_other_tenant(pg_request_db, pg_admin_request_db):
    tenant_a, tenant_b, billing_a, billing_b = seed_two_tenants(pg_request_db)

    response = post_webhook(billing_a, payment_id="pay_a")
    assert response.status_code == 200, response.text

    # Tenant B intocado.
    [b_billing] = admin_read(pg_admin_request_db, BillingRequest, id=billing_b)
    assert b_billing.status == "checkout_pending"
    assert b_billing.paid_at is None
    assert b_billing.provider_reference is None
    [b_sub] = admin_read(pg_admin_request_db, Subscription, tenant_id=tenant_b)
    assert b_sub.status == "trial"
    assert b_sub.plan_type == "basic"

    # Runtime com contexto do tenant A não enxerga dados de B.
    db = pg_request_db()
    try:
        set_tenant_on_session(db, tenant_a)
        assert db.query(BillingRequest).filter(BillingRequest.id == billing_b).one_or_none() is None
        assert db.query(Subscription).filter(Subscription.tenant_id == tenant_b).one_or_none() is None
        assert {s.tenant_id for s in db.query(Subscription).all()} == {tenant_a}
    finally:
        db.close()


def test_mutation_happens_through_runtime_role_with_tenant_context(
    pg_request_db, pg_admin_request_db, pg_app_database_url, pg_admin_database_url
):
    tenant_a, tenant_b, billing_a, billing_b = seed_two_tenants(pg_request_db)
    runtime_role = make_url(pg_app_database_url).username
    admin_role = make_url(pg_admin_database_url).username
    flushes = []

    def _record_flush(session, flush_context):
        row = session.connection().execute(
            text("SELECT current_user, current_setting('app.tenant_id', true)")
        ).one()
        flushes.append((row[0], row[1]))

    event.listen(Session, "after_flush", _record_flush)
    try:
        response = post_webhook(billing_a, payment_id="pay_a")
    finally:
        event.remove(Session, "after_flush", _record_flush)

    assert response.status_code == 200, response.text
    assert flushes, "a mutação deveria ter ocorrido via flush de uma Session"
    assert set(flushes) == {(runtime_role, str(tenant_a))}
    assert admin_role not in {user for user, _ in flushes}

    # A role admin é somente leitura: qualquer escrita por ela falharia (42501).
    admin_db = pg_admin_request_db()
    try:
        with pytest.raises(DBAPIError) as exc_info:
            admin_db.execute(
                text("UPDATE billing_requests SET status = 'paid' WHERE id = :id"), {"id": billing_b}
            )
        assert getattr(exc_info.value.orig, "pgcode", None) == "42501"
    finally:
        admin_db.rollback()
        admin_db.close()


def test_admin_database_unavailable_fails_closed(monkeypatch, pg_request_db, pg_admin_request_db):
    tenant_a, tenant_b, billing_a, billing_b = seed_two_tenants(pg_request_db)

    def _unavailable():
        raise AdminDatabaseNotConfigured("ADMIN_DATABASE_URL is not configured")

    monkeypatch.setattr(db_session_module, "AdminSessionLocal", _unavailable)

    response = post_webhook(billing_a, payment_id="pay_a")
    # Não-2xx: o provedor não considera o pagamento processado e reenvia.
    assert response.status_code == 503
    assert response.json() == {"detail": "admin database unavailable"}

    [billing] = admin_read(pg_admin_request_db, BillingRequest, id=billing_a)
    assert billing.status == "checkout_pending"
    assert billing.paid_at is None
    assert admin_read(pg_admin_request_db, Subscription, tenant_id=tenant_a) == []
