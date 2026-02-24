from sqlalchemy.orm import Session
from sqlalchemy import text


def register_usage(db: Session, tenant_id: int, event_type: str, resource_id: int | None = None) -> None:
    """
    Registra um evento de uso do tenant.
    Exemplo: case_created, analysis_generated, pdf_generated
    """
    db.execute(
        text(
            """
            INSERT INTO tenant_usage_events (tenant_id, event_type, resource_id)
            VALUES (:tenant_id, :event_type, :resource_id)
            """
        ),
        {
            "tenant_id": tenant_id,
            "event_type": event_type,
            "resource_id": resource_id,
        },
    )

# ================================
# SaaS Usage Summary Engine
# ================================

from sqlalchemy import func
from app.models import TenantUsageEvent, Tenant


PLAN_LIMITS = {
    "free": 5,
    "basic": 20,
    "pro": 100,
    "elite": None,  # ilimitado
}


def get_usage_summary(db, tenant_id: int):
    plan = db.query(Tenant.plan).filter(Tenant.id == tenant_id).scalar()

    cases_created = (
        db.query(func.count(TenantUsageEvent.id))
        .filter(
            TenantUsageEvent.tenant_id == tenant_id,
            TenantUsageEvent.event_type == "case_created",
        )
        .scalar()
    )

    limit = PLAN_LIMITS.get(plan)

    if limit is None:
        remaining = None
    else:
        remaining = max(limit - cases_created, 0)

    return {
        "tenant_id": tenant_id,
        "plan": plan,
        "cases_created": cases_created,
        "limit": limit,
        "remaining": remaining,
    }

