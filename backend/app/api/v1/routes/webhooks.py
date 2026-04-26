from __future__ import annotations

import hmac
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.plans import PlanType, limits_for
from app.core.settings import settings
from app.db.session import get_db
from app.models.billing_request import BillingRequest
from app.models.subscription import Subscription

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

PAYMENT_EVENTS_TO_PROCESS = {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED", "PAYMENT_UPDATED"}
PAYMENT_STATUSES_PAID = {"RECEIVED", "CONFIRMED"}


def _authorized(token: str | None) -> bool:
    expected = (settings.ASAAS_WEBHOOK_TOKEN or "").strip()
    provided = (token or "").strip()
    return bool(expected and provided and hmac.compare_digest(provided, expected))


def _payment_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payment = payload.get("payment")
    return payment if isinstance(payment, dict) else {}


@router.post("/asaas")
async def asaas_webhook(
    request: Request,
    asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"),
    db: Session = Depends(get_db),
):
    if not _authorized(asaas_access_token):
        logger.warning("asaas webhook rejected: invalid token")
        raise HTTPException(status_code=403, detail="Webhook token inválido.")

    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            logger.warning("asaas webhook ignored: non-object payload")
            return {"ok": True, "ignored": "invalid_payload"}

        event = str(payload.get("event") or "").strip()
        payment = _payment_payload(payload)
        payment_id = str(payment.get("id") or "").strip()
        status = str(payment.get("status") or "").strip().upper()
        external_reference = str(payment.get("externalReference") or "").strip()

        logger.info(
            "asaas webhook received event=%s status=%s payment_id=%s external_reference=%s",
            event,
            status,
            payment_id,
            external_reference,
        )

        if event not in PAYMENT_EVENTS_TO_PROCESS:
            return {"ok": True, "ignored_event": event}

        if status not in PAYMENT_STATUSES_PAID:
            return {"ok": True, "ignored_status": status}

        if not external_reference.isdigit():
            return {"ok": True, "ignored_reference": external_reference}

        billing_id = int(external_reference)

        billing = db.query(BillingRequest).filter(BillingRequest.id == billing_id).one_or_none()
        if billing is None:
            return {"ok": True, "missing_billing_request": billing_id}

        if billing.status == "paid":
            return {
                "ok": True,
                "already_paid": billing.id,
                "provider_reference": billing.provider_reference,
            }

        if billing.status in {"canceled", "expired", "failed"}:
            return {
                "ok": True,
                "ignored_billing_status": billing.status,
                "billing_request_id": billing.id,
            }

        requested_plan = PlanType(billing.requested_plan_type)
        lim = limits_for(requested_plan)

        paid_at = datetime.now(timezone.utc)
        new_expires_at = paid_at + timedelta(days=30)

        sub = db.query(Subscription).filter(Subscription.tenant_id == billing.tenant_id).one_or_none()

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
        billing.provider_reference = payment_id or billing.provider_reference

        db.commit()

        return {
            "ok": True,
            "billing_request_id": billing.id,
            "tenant_id": billing.tenant_id,
            "plan_type": billing.requested_plan_type,
            "provider_reference": billing.provider_reference,
        }

    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("asaas webhook failed due to database error")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook Asaas.")
    except Exception:
        db.rollback()
        logger.exception("asaas webhook failed unexpectedly")
        raise HTTPException(status_code=500, detail="Erro inesperado ao processar webhook Asaas.")
