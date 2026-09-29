import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.tenant import set_tenant_on_session
from app.models.case import Case
from app.models.tenant import Tenant


pytestmark = pytest.mark.pg


def _sqlstate(exc: DBAPIError) -> str | None:
    orig = exc.orig
    return getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)


def create_tenant(db, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_case(db, tenant: Tenant, case_number: str) -> Case:
    set_tenant_on_session(db, tenant.id)
    case = Case(
        case_number=case_number,
        title=f"Caso {case_number}",
        description=f"Descrição {case_number}",
        status="draft",
        tenant_id=tenant.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_rls_isolation(pg_request_db):
    db = pg_request_db()
    try:
        tenant_a = create_tenant(db, "Tenant A")
        tenant_b = create_tenant(db, "Tenant B")

        create_case(db, tenant_a, "A-001")
        create_case(db, tenant_b, "B-001")

        set_tenant_on_session(db, tenant_a.id)
        results_a = db.query(Case).order_by(Case.id).all()

        set_tenant_on_session(db, tenant_b.id)
        results_b = db.query(Case).order_by(Case.id).all()

        assert [case.case_number for case in results_a] == ["A-001"]
        assert [case.case_number for case in results_b] == ["B-001"]
    finally:
        db.close()


def test_rls_fail_closed_without_or_with_invalid_tenant(pg_request_db):
    seed = pg_request_db()
    try:
        tenant = create_tenant(seed, "Tenant Fail Closed")
        create_case(seed, tenant, "FC-001")
    finally:
        seed.close()

    db = pg_request_db()
    try:
        # Sessão nova sem tenant: nenhuma linha protegida é visível.
        assert db.query(Case).all() == []

        # Valor inválido deve negar acesso, não provocar erro de cast.
        db.execute(text("SELECT set_config('app.tenant_id', 'abc', true)"))
        assert db.query(Case).all() == []

        db.execute(text("SELECT set_config('app.tenant_id', '', true)"))
        assert db.query(Case).all() == []

        db.execute(text("SELECT set_config('app.tenant_id', '0', true)"))
        assert db.query(Case).all() == []
    finally:
        db.close()


def test_rls_rejects_cross_tenant_insert(pg_request_db):
    db = pg_request_db()
    try:
        tenant_a = create_tenant(db, "Tenant Write A")
        tenant_b = create_tenant(db, "Tenant Write B")

        set_tenant_on_session(db, tenant_a.id)
        db.add(
            Case(
                case_number="B-BLOCKED",
                title="Não pode gravar",
                description="Tentativa cross-tenant",
                status="draft",
                tenant_id=tenant_b.id,
            )
        )

        with pytest.raises(DBAPIError) as exc_info:
            db.commit()

        assert _sqlstate(exc_info.value) == "42501"
        db.rollback()
    finally:
        db.close()


def test_rls_admin_reads_all_but_cannot_mutate(
    pg_request_db,
    pg_admin_request_db,
):
    runtime = pg_request_db()
    try:
        tenant_a = create_tenant(runtime, "Tenant Admin A")
        tenant_b = create_tenant(runtime, "Tenant Admin B")
        case_a = create_case(runtime, tenant_a, "ADM-A")
        create_case(runtime, tenant_b, "ADM-B")
        case_a_id = case_a.id
    finally:
        runtime.close()

    admin = pg_admin_request_db()
    try:
        rows = admin.query(Case).order_by(Case.case_number).all()
        assert [case.case_number for case in rows] == ["ADM-A", "ADM-B"]

        with pytest.raises(DBAPIError) as exc_info:
            admin.execute(
                text("UPDATE cases SET title = :title WHERE id = :id"),
                {"title": "Admin não deve alterar", "id": case_a_id},
            )
            admin.commit()

        assert _sqlstate(exc_info.value) == "42501"
        admin.rollback()
    finally:
        admin.close()
