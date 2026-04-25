from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.billing_request import BillingRequest
from app.models.subscription import Subscription
from app.core.plans import PlanType, limits_for
from app.core.settings import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _authorized(token: str | None) -> bool:
    expected = (settings.ASAAS_WEBHOOK_TOKEN or "").strip()
    provided = (token or "").strip()
    return bool(expected and provided and expected == provided)


@router.post("/asaas")
async def asaas_webhook(
    request: Request,
    asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"),
    db: Session = Depends(get_db),
):
    if not _authorized(asaas_access_token):
        raise HTTPException(status_code=403, detail="Webhook token inválido.")

    payload = await request.json()

    event = payload.get("event")
    payment = payload.get("payment") or {}

    if event not in {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED", "PAYMENT_UPDATED"}:
        return {"ok": True, "ignored": event}

    status = (payment.get("status") or "").upper()
    if status not in {"RECEIVED", "CONFIRMED"}:
        return {"ok": True, "ignored_status": status}

    external_reference = str(payment.get("externalReference") or "").strip()
    if not external_reference.isdigit():
        return {"ok": True, "ignored_reference": external_reference}

    billing_id = int(external_reference)

    billing = db.query(BillingRequest).filter(BillingRequest.id == billing_id).one_or_none()
    if billing is None:
        return {"ok": True, "missing_billing_request": billing_id}

    if billing.status == "paid":
        return {"ok": True, "already_paid": billing.id}

    requested_plan = PlanType(billing.requested_plan_type)
    lim = limits_for(requested_plan)

    paid_at = datetime.now(timezone.utc)
    new_expires_at = paid_at + timedelta(days=30)

    sub = db.query(Subscription).filter(
        Subscription.tenant_id == billing.tenant_id
    ).one_or_none()

    if sub is None:
        sub = Subscription(
            tenant_id=billing.tenant_id,
            plan_type=billing.requested_plan_type,
            status="active",
            case_limit=lim.cases_per_month,
            active=True,
            expires_at=new_expires_at,
        )
        db.add(sub)
    else:
        sub.plan_type = billing.requested_plan_type
        sub.status = "active"
        sub.case_limit = lim.cases_per_month
        sub.active = True
        sub.expires_at = new_expires_at

    billing.status = "paid"
    billing.paid_at = paid_at
    billing.provider_reference = payment.get("id") or billing.provider_reference

    db.commit()

    return {
        "ok": True,
        "billing_request_id": billing.id,
        "tenant_id": billing.tenant_id,
        "plan_type": billing.requested_plan_type,
    }
