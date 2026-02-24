import pytest
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.case import Case


def create_tenant(db, name):
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def test_rls_isolation():
    db = SessionLocal()

    # Criar dois tenants
    tenant_a = create_tenant(db, "Tenant A")
    tenant_b = create_tenant(db, "Tenant B")

    # Inserir caso no Tenant A
    db.execute(text("SET app.tenant_id = :tid"), {"tid": tenant_a.id})
    case_a = Case(
        case_number="A-001",
        title="Caso A",
        description="Desc A",
        status="draft",
        tenant_id=tenant_a.id
    )
    db.add(case_a)
    db.commit()

    # Inserir caso no Tenant B
    db.execute(text("SET app.tenant_id = :tid"), {"tid": tenant_b.id})
    case_b = Case(
        case_number="B-001",
        title="Caso B",
        description="Desc B",
        status="draft",
        tenant_id=tenant_b.id
    )
    db.add(case_b)
    db.commit()

    # Consultar como Tenant A
    db.execute(text("SET app.tenant_id = :tid"), {"tid": tenant_a.id})
    results_a = db.query(Case).all()

    # Consultar como Tenant B
    db.execute(text("SET app.tenant_id = :tid"), {"tid": tenant_b.id})
    results_b = db.query(Case).all()

    assert len(results_a) == 1
    assert results_a[0].case_number == "A-001"

    assert len(results_b) == 1
    assert results_b[0].case_number == "B-001"

    db.close()
