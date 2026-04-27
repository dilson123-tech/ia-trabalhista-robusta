from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.db.session import get_db
from app.api.v1.routes.admin import (
    BillingRequestCreateIn,
    BillingRequestCheckoutIn,
    PLAN_ORDER,
    admin_create_billing_request,
    admin_create_billing_checkout_session,
)
from app.services.plan_enforcement import get_effective_plan

router = APIRouter(prefix="/billing", tags=["billing"])


class PlanChangeIn(BaseModel):
    requested_plan_type: str = Field(..., description="basic|pro|office")


@router.post("/plan-change")
def create_plan_change_checkout(
    payload: PlanChangeIn,
    claims=Depends(require_auth),
    db: Session = Depends(get_db),
):
    tenant_id = claims["tenant_id"]

    eff = get_effective_plan(db, tenant_id)
    current_plan_type = getattr(eff.plan_type, "value", str(eff.plan_type))
    requested_plan_type = payload.requested_plan_type

    if requested_plan_type == current_plan_type:
        raise HTTPException(status_code=422, detail="Você já está neste plano.")

    billing_reason = (
        "plan_upgrade"
        if PLAN_ORDER.get(requested_plan_type, 0) > PLAN_ORDER.get(current_plan_type, 0)
        else "plan_downgrade"
    )

    created = admin_create_billing_request(
        tenant_id=tenant_id,
        payload=BillingRequestCreateIn(
            requested_plan_type=requested_plan_type,
            payment_method="pix",
            payment_provider="asaas",
            billing_reason=billing_reason,
        ),
        db=db,
    )

    billing_id = created["billing_request"]["id"]

    checkout = admin_create_billing_checkout_session(
        billing_request_id=billing_id,
        payload=BillingRequestCheckoutIn(
            payment_method="pix",
            payment_provider="asaas",
        ),
        db=db,
    )

    return checkout
