from sqlalchemy.orm import Session
from app.core.plans import limits_for
from app.services.plan_enforcement import get_effective_plan, get_case_capacity_summary
from app.models.usage_counter import UsageCounter
from fastapi import Depends
from app.db.session import get_db
from app.models import TenantUsageEvent
from app.core.security import require_auth
from fastapi import Depends
from app.core.security import require_auth
from fastapi import APIRouter

from datetime import date
router = APIRouter(
    prefix="/usage",
    tags=["usage"],
)


@router.get("/summary")
def usage_summary(
    claims=Depends(require_auth),
    db: Session = Depends(get_db),
):
    total = db.query(TenantUsageEvent).filter(TenantUsageEvent.tenant_id == claims["tenant_id"]).count()
    return {"tenant_id": claims["tenant_id"], "total_events": total}


@router.get("/summary-v2")
def usage_summary_v2(
    claims=Depends(require_auth),
    db: Session = Depends(get_db),
):
    tenant_id = claims["tenant_id"]
    month = date.today().replace(day=1)

    eff = get_effective_plan(db, tenant_id)
    lim = limits_for(eff.plan_type)

    row = (
        db.query(UsageCounter)
        .filter(UsageCounter.tenant_id == tenant_id, UsageCounter.month == month)
        .one_or_none()
    )

    used_cases = int(getattr(row, "cases_created", 0) or 0)
    used_ai = int(getattr(row, "ai_analyses_generated", 0) or 0)

    remaining_cases = max(lim.cases_per_month - used_cases, 0)
    remaining_ai = max(lim.ai_analyses_per_month - used_ai, 0)
    storage = get_case_capacity_summary(db, tenant_id)

    return {
        "tenant_id": tenant_id,
        "month": month.isoformat(),
        "plan": {"type": getattr(eff.plan_type, "value", str(eff.plan_type)), "status": str(eff.status)},
        "limits": {
            "cases_per_month": lim.cases_per_month,
            "active_cases": storage.active_cases_limit,
            "case_records": storage.case_records_limit,
            "ai_analyses_per_month": lim.ai_analyses_per_month,
        },
        "used": {
            "cases_created": used_cases,
            "ai_analyses_generated": used_ai,
            "active_cases": storage.active_cases,
            "archived_cases": storage.archived_cases,
            "case_records": storage.case_records,
        },
        "remaining": {
            "cases": remaining_cases,
            "ai_analyses": remaining_ai,
            "active_cases": storage.remaining_active_cases,
            "case_records": storage.remaining_case_records,
        },
    }
