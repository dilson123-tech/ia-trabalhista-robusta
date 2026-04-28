from __future__ import annotations

import os
import hmac
import logging
import csv
import io
from datetime import datetime, timezone, date, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from app.core.plans import PlanType, limits_for
from app.core.tenant import set_tenant_on_session
from app.core.security import pwd_context
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.billing_request import BillingRequest
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.usage_counter import UsageCounter
from app.models.tenant_usage_event import TenantUsageEvent
from app.models.user import User
from app.services.plan_enforcement import get_effective_plan
from app.services.payment_checkout import PaymentCheckoutError, create_checkout_session

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

PLAN_MONTHLY_PRICES_CENTS = {
    "basic": 24700,
    "pro": 49700,
    "office": 109700,
}

PLAN_ORDER = {
    "basic": 1,
    "pro": 2,
    "office": 3,
}



def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    # Suporta rotação: ADMIN_API_KEYS="k1,k2" e legado ADMIN_API_KEY
    raw_multi = (os.getenv("ADMIN_API_KEYS", "") or "").strip()
    keys = {k.strip() for k in raw_multi.split(",") if k.strip()}

    legacy = (os.getenv("ADMIN_API_KEY", "") or "").strip()
    if legacy:
        keys.add(legacy)

    if not keys:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY(S) não configurada(s) no ambiente.")

    if not x_admin_key:
        raise HTTPException(status_code=403, detail="Admin key inválida.")

    provided = x_admin_key.strip()
    ok = any(hmac.compare_digest(provided, k) for k in keys)
    if not ok:
        raise HTTPException(status_code=403, detail="Admin key inválida.")

def _reset_tenant_context(db: Session) -> None:
    """
    Best-effort: garante que app.tenant_id não vaze pra próxima request no pool.
    Em SQLite/dev, isso vira no-op.
    """
    try:
        bind = db.get_bind()
        dialect = getattr(getattr(bind, "dialect", None), "name", "") or ""
        if str(dialect).startswith("postgres"):
            db.execute(text("RESET app.tenant_id"))
        # garante sessão limpinha
        try:
            db.rollback()
        except Exception:
            pass
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


class SubscriptionActiveToggleIn(BaseModel):
    active: bool = Field(..., description="true para ativar, false para desativar")


class SubscriptionUpsertIn(BaseModel):
    plan_type: str = Field(..., description="basic|pro|office")
    status: str = Field(..., description="trial|active|canceled")
    expires_at: Optional[datetime] = Field(default=None, description="ISO datetime (UTC recomendado)")


class OnboardingBootstrapIn(BaseModel):
    tenant_name: str = Field(..., min_length=3, max_length=150, description="Nome do tenant/escritório")
    username: str = Field(..., min_length=3, max_length=80, description="Usuário responsável inicial")
    password: str = Field(..., min_length=8, max_length=128, description="Senha inicial do responsável")
    trial_days: int = Field(default=7, ge=1, le=30, description="Duração do trial inicial em dias")


class BillingRequestCreateIn(BaseModel):
    requested_plan_type: str = Field(..., description="basic|pro|office")
    payment_method: str = Field(..., description="pix|credit_card|debit_card")
    payment_provider: str = Field(default="manual", max_length=30, description="Identificador do provedor de pagamento")
    billing_reason: str = Field(default="plan_upgrade", description="plan_upgrade|plan_downgrade|plan_renewal|validation_test")
    custom_amount_cents: Optional[int] = Field(default=None, ge=100, le=5000, description="Valor customizado em centavos para validation_test")


class BillingRequestMarkPaidIn(BaseModel):
    payment_method: Optional[str] = Field(default=None, description="pix|credit_card|debit_card")
    provider_reference: Optional[str] = Field(default=None, max_length=120)
    paid_at: Optional[datetime] = Field(default=None, description="ISO datetime (UTC recomendado)")


class BillingRequestCheckoutIn(BaseModel):
    payment_method: Optional[str] = Field(default=None, description="pix|credit_card|debit_card")
    payment_provider: Optional[str] = Field(default=None, max_length=30, description="Provider desejado para o checkout")


@router.post("/tenants/{tenant_id}/billing-requests", dependencies=[Depends(require_admin_key)])
def admin_create_billing_request(
    tenant_id: int,
    payload: BillingRequestCreateIn,
    db: Session = Depends(get_db),
):
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant não encontrado.")

        try:
            requested_plan = PlanType(payload.requested_plan_type)
        except Exception:
            raise HTTPException(status_code=422, detail="requested_plan_type inválido (use basic|pro|office).")

        if payload.payment_method not in ("pix", "credit_card", "debit_card"):
            raise HTTPException(status_code=422, detail="payment_method inválido (use pix|credit_card|debit_card).")

        if payload.billing_reason not in ("plan_upgrade", "plan_downgrade", "plan_renewal", "validation_test"):
            raise HTTPException(status_code=422, detail="billing_reason inválido (use plan_upgrade|plan_downgrade|plan_renewal|validation_test).")

        eff = get_effective_plan(db, tenant_id)
        current_plan_type = getattr(eff.plan_type, "value", str(eff.plan_type))
        requested_plan_type = getattr(requested_plan, "value", str(requested_plan))

        if payload.billing_reason == "validation_test":
            requested_plan_type = current_plan_type
            amount_cents = payload.custom_amount_cents
            if amount_cents is None or amount_cents <= 0:
                raise HTTPException(status_code=422, detail="validation_test exige custom_amount_cents > 0.")
        else:
            if payload.billing_reason == "plan_upgrade":
                if PLAN_ORDER.get(requested_plan_type, 0) <= PLAN_ORDER.get(current_plan_type, 0):
                    raise HTTPException(status_code=422, detail="plan_upgrade exige plano superior ao atual.")

            amount_cents = PLAN_MONTHLY_PRICES_CENTS.get(requested_plan_type)
            if amount_cents is None:
                raise HTTPException(status_code=422, detail="Preço do plano solicitado não configurado.")

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        billing = BillingRequest(
            tenant_id=tenant_id,
            requested_plan_type=requested_plan_type,
            current_plan_type=current_plan_type,
            billing_reason=payload.billing_reason,
            payment_method=payload.payment_method,
            payment_provider=(payload.payment_provider or "manual").strip() or "manual",
            amount_cents=amount_cents,
            currency="BRL",
            status="requested",
            expires_at=expires_at,
        )
        db.add(billing)
        db.commit()
        db.refresh(billing)

        return {
            "tenant_id": tenant_id,
            "billing_request": {
                "id": billing.id,
                "current_plan_type": billing.current_plan_type,
                "requested_plan_type": billing.requested_plan_type,
                "billing_reason": billing.billing_reason,
                "payment_method": billing.payment_method,
                "payment_provider": billing.payment_provider,
                "amount_cents": billing.amount_cents,
                "currency": billing.currency,
                "status": billing.status,
                "expires_at": billing.expires_at.isoformat() if billing.expires_at else None,
                "created_at": billing.created_at.isoformat() if getattr(billing, "created_at", None) else None,
            },
            "next_step": "Conectar esta billing_request ao checkout real (PIX/cartão) antes de automatizar a troca de plano.",
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin create billing request failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin create billing request failed: SQLAlchemyError: {e}")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin create billing request failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin create billing request failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)


@router.post("/billing-requests/{billing_request_id}/checkout-session", dependencies=[Depends(require_admin_key)])
def admin_create_billing_checkout_session(
    billing_request_id: int,
    payload: BillingRequestCheckoutIn,
    db: Session = Depends(get_db),
):
    try:
        billing = (
            db.query(BillingRequest)
            .filter(BillingRequest.id == billing_request_id)
            .one_or_none()
        )
        if billing is None:
            raise HTTPException(status_code=404, detail="Billing request não encontrada.")

        if billing.status in ("paid", "canceled", "expired", "failed"):
            raise HTTPException(status_code=409, detail="Billing request não permite novo checkout no status atual.")

        payment_method = (payload.payment_method or billing.payment_method or "").strip()
        if payment_method not in ("pix", "credit_card", "debit_card"):
            raise HTTPException(status_code=422, detail="payment_method inválido (use pix|credit_card|debit_card).")

        requested_provider = (payload.payment_provider or billing.payment_provider or "").strip() or None

        session = create_checkout_session(
            billing_request_id=billing.id,
            tenant_id=billing.tenant_id,
            amount_cents=billing.amount_cents,
            currency=billing.currency,
            payment_method=payment_method,
            requested_plan_type=billing.requested_plan_type,
            payment_provider=requested_provider,
        )

        billing.payment_method = payment_method
        billing.payment_provider = session.provider
        billing.provider_reference = session.provider_reference
        billing.checkout_url = session.checkout_url
        billing.status = "checkout_pending"
        if session.expires_at is not None:
            billing.expires_at = session.expires_at

        db.commit()
        db.refresh(billing)

        return {
            "billing_request": {
                "id": billing.id,
                "tenant_id": billing.tenant_id,
                "status": billing.status,
                "current_plan_type": billing.current_plan_type,
                "requested_plan_type": billing.requested_plan_type,
                "payment_method": billing.payment_method,
                "payment_provider": billing.payment_provider,
                "provider_reference": billing.provider_reference,
                "amount_cents": billing.amount_cents,
                "currency": billing.currency,
                "checkout_url": billing.checkout_url,
                "expires_at": billing.expires_at.isoformat() if billing.expires_at else None,
            },
            "checkout": {
                "provider": session.provider,
                "provider_reference": session.provider_reference,
                "checkout_url": session.checkout_url,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "raw_payload": session.raw_payload,
            },
            "next_step": "Conectar provider real de PIX/cartão e depois webhook para confirmação automática.",
        }

    except HTTPException:
        raise
    except PaymentCheckoutError as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=422, detail=str(e))
    except SQLAlchemyError as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin create billing checkout session failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin create billing checkout session failed: SQLAlchemyError: {e}")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin create billing checkout session failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin create billing checkout session failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)


@router.get("/tenants/{tenant_id}/billing-requests", dependencies=[Depends(require_admin_key)])
def admin_list_billing_requests(
    tenant_id: int,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant não encontrado.")

        q = db.query(BillingRequest).filter(BillingRequest.tenant_id == tenant_id)

        if status:
            q = q.filter(BillingRequest.status == status)

        rows = (
            q.order_by(BillingRequest.created_at.desc(), BillingRequest.id.desc())
            .limit(limit)
            .all()
        )

        items = [
            {
                "id": row.id,
                "current_plan_type": row.current_plan_type,
                "requested_plan_type": row.requested_plan_type,
                "billing_reason": row.billing_reason,
                "payment_method": row.payment_method,
                "payment_provider": row.payment_provider,
                "amount_cents": row.amount_cents,
                "currency": row.currency,
                "status": row.status,
                "provider_reference": row.provider_reference,
                "checkout_url": row.checkout_url,
                "expires_at": row.expires_at.isoformat() if getattr(row, "expires_at", None) else None,
                "paid_at": row.paid_at.isoformat() if getattr(row, "paid_at", None) else None,
                "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
            }
            for row in rows
        ]

        return {
            "tenant_id": tenant_id,
            "count": len(items),
            "limit": limit,
            "items": items,
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin list billing requests failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin list billing requests failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin list billing requests failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin list billing requests failed: {type(e).__name__}: {e}")


@router.patch("/billing-requests/{billing_request_id}/mark-paid", dependencies=[Depends(require_admin_key)])
def admin_mark_billing_request_paid(
    billing_request_id: int,
    payload: BillingRequestMarkPaidIn,
    db: Session = Depends(get_db),
):
    try:
        billing = (
            db.query(BillingRequest)
            .filter(BillingRequest.id == billing_request_id)
            .one_or_none()
        )
        if billing is None:
            raise HTTPException(status_code=404, detail="Billing request não encontrada.")

        if billing.status in ("canceled", "expired", "failed"):
            raise HTTPException(status_code=409, detail="Billing request não pode ser marcada como paga no status atual.")

        if payload.payment_method is not None and payload.payment_method not in ("pix", "credit_card", "debit_card"):
            raise HTTPException(status_code=422, detail="payment_method inválido (use pix|credit_card|debit_card).")

        paid_at = payload.paid_at or datetime.now(timezone.utc)
        if paid_at.tzinfo is None:
            paid_at = paid_at.replace(tzinfo=timezone.utc)

        requested_plan = PlanType(billing.requested_plan_type)
        lim = limits_for(requested_plan)
        new_expires_at = paid_at + timedelta(days=30)

        sub = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == billing.tenant_id)
            .one_or_none()
        )

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

        if payload.payment_method:
            billing.payment_method = payload.payment_method
        if payload.provider_reference is not None:
            billing.provider_reference = payload.provider_reference.strip() or None

        billing.status = "paid"
        billing.paid_at = paid_at

        db.commit()
        db.refresh(billing)
        db.refresh(sub)

        return {
            "billing_request": {
                "id": billing.id,
                "tenant_id": billing.tenant_id,
                "status": billing.status,
                "payment_method": billing.payment_method,
                "provider_reference": billing.provider_reference,
                "paid_at": billing.paid_at.isoformat() if billing.paid_at else None,
                "requested_plan_type": billing.requested_plan_type,
            },
            "subscription": {
                "tenant_id": sub.tenant_id,
                "plan_type": sub.plan_type,
                "status": sub.status,
                "active": bool(sub.active),
                "case_limit": sub.case_limit,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            },
            "next_step": "Conectar confirmação automática do gateway/webhook para dispensar baixa manual.",
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin mark billing request paid failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin mark billing request paid failed: SQLAlchemyError: {e}")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin mark billing request paid failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin mark billing request paid failed: {type(e).__name__}: {e}")


@router.get("/audit/logs", dependencies=[Depends(require_admin_key)])
def admin_audit_logs(
    tenant_id: Optional[int] = Query(default=None),
    status_code: Optional[int] = Query(default=None),
    path: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        q = db.query(AuditLog)

        if tenant_id is not None:
            q = q.filter(AuditLog.tenant_id == tenant_id)

        if status_code is not None:
            q = q.filter(AuditLog.status_code == status_code)

        if path:
            q = q.filter(AuditLog.path == path)

        rows = (
            q.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
            .all()
        )

        items = [
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "request_id": row.request_id,
                "method": row.method,
                "path": row.path,
                "status_code": row.status_code,
                "process_time_ms": row.process_time_ms,
                "username": row.username,
                "role": row.role,
                "client_ip": row.client_ip,
                "user_agent": row.user_agent,
                "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None,
            }
            for row in rows
        ]

        return {
            "count": len(items),
            "limit": limit,
            "items": items,
        }

    except SQLAlchemyError as e:
        logger.exception("admin audit logs failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin audit logs failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin audit logs failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin audit logs failed: {type(e).__name__}: {e}")


@router.get("/dashboard/summary", dependencies=[Depends(require_admin_key)])
def admin_dashboard_summary(
    db: Session = Depends(get_db),
):
    try:
        tenants_total = db.query(Tenant).count()
        users_total = db.query(User).count()
        subscriptions_total = db.query(Subscription).count()

        subscriptions_active = db.query(Subscription).filter(Subscription.status == "active").count()
        subscriptions_trial = db.query(Subscription).filter(Subscription.status == "trial").count()
        subscriptions_canceled = db.query(Subscription).filter(Subscription.status == "canceled").count()

        subscriptions_active_flag_true = db.query(Subscription).filter(Subscription.active.is_(True)).count()
        subscriptions_active_flag_false = db.query(Subscription).filter(Subscription.active.is_(False)).count()

        plan_rows = (
            db.query(Subscription.plan_type, func.count(Subscription.id))
            .group_by(Subscription.plan_type)
            .all()
        )
        subscriptions_by_plan = {"basic": 0, "pro": 0, "office": 0}
        for plan_type, total in plan_rows:
            subscriptions_by_plan[str(plan_type)] = int(total)

        return {
            "tenants_total": tenants_total,
            "users_total": users_total,
            "subscriptions_total": subscriptions_total,
            "subscriptions_active": subscriptions_active,
            "subscriptions_trial": subscriptions_trial,
            "subscriptions_canceled": subscriptions_canceled,
            "subscriptions_active_flag_true": subscriptions_active_flag_true,
            "subscriptions_active_flag_false": subscriptions_active_flag_false,
            "subscriptions_by_plan": subscriptions_by_plan,
        }

    except SQLAlchemyError as e:
        logger.exception("admin dashboard summary failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin dashboard summary failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin dashboard summary failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin dashboard summary failed: {type(e).__name__}: {e}")


@router.post("/onboarding/bootstrap", dependencies=[Depends(require_admin_key)])
def admin_onboarding_bootstrap(
    payload: OnboardingBootstrapIn,
    db: Session = Depends(get_db),
):
    """
    Cria onboarding mínimo oficial:
    - tenant
    - usuário responsável inicial
    - membership admin
    - subscription basic/trial
    """
    try:
        tenant_name = (payload.tenant_name or "").strip()
        username = (payload.username or "").strip()

        if not tenant_name:
            raise HTTPException(status_code=422, detail="tenant_name é obrigatório")
        if not username:
            raise HTTPException(status_code=422, detail="username é obrigatório")

        existing_tenant = db.query(Tenant).filter(Tenant.name == tenant_name).one_or_none()
        if existing_tenant is not None:
            raise HTTPException(status_code=409, detail="tenant name already exists")

        existing_user = db.query(User).filter(User.username == username).one_or_none()
        if existing_user is not None:
            raise HTTPException(status_code=409, detail="username already exists")

        tenant = Tenant(
            name=tenant_name,
            plan="basic",
        )
        db.add(tenant)
        db.flush()

        set_tenant_on_session(db, tenant.id)

        trial_expires_at = datetime.now(timezone.utc) + timedelta(days=payload.trial_days)
        lim = limits_for(PlanType.basic)

        sub = Subscription(
            tenant_id=tenant.id,
            plan_type="basic",
            status="trial",
            case_limit=lim.cases_per_month,
            active=True,
            expires_at=trial_expires_at,
        )
        db.add(sub)

        user = User(
            username=username,
            password_hash=pwd_context.hash(payload.password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()

        membership = TenantMember(
            tenant_id=tenant.id,
            user_id=user.id,
            role="admin",
        )
        db.add(membership)

        db.commit()
        db.refresh(tenant)
        db.refresh(user)
        db.refresh(sub)

        return {
            "tenant": {
                "tenant_id": tenant.id,
                "name": tenant.name,
                "plan": tenant.plan,
                "created_at": tenant.created_at.isoformat() if getattr(tenant, "created_at", None) else None,
            },
            "user": {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": bool(user.is_active),
            },
            "subscription": {
                "plan_type": sub.plan_type,
                "status": sub.status,
                "active": bool(sub.active),
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            },
            "next_steps": {
                "login_path": "/api/v1/auth/login",
                "smoke_flow": [
                    "login",
                    "create_case",
                    "read_case",
                    "analysis",
                    "executive_summary",
                    "executive_report",
                    "executive_pdf",
                ],
            },
        }

    except HTTPException:
        raise
    except IntegrityError:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=409, detail="tenant or username already exists")
    except SQLAlchemyError as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin onboarding bootstrap failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin onboarding bootstrap failed: SQLAlchemyError: {e}")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin onboarding bootstrap failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin onboarding bootstrap failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)


@router.get("/tenants", dependencies=[Depends(require_admin_key)])
def admin_list_tenants(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    plan_type: Optional[str] = Query(default=None, description="basic|pro|office"),
    status: Optional[str] = Query(default=None, description="trial|active|canceled"),
    name: Optional[str] = Query(default=None, description="Busca por nome do tenant"),
    db: Session = Depends(get_db),
):
    """
    Lista global de tenants para operação/admin.
    Não usa set_tenant_on_session: visão global de backoffice.
    """
    try:
        q = (
            db.query(Tenant, Subscription)
            .outerjoin(Subscription, Subscription.tenant_id == Tenant.id)
        )

        if plan_type:
            q = q.filter(Subscription.plan_type == plan_type)

        if status:
            q = q.filter(Subscription.status == status)

        if name:
            q = q.filter(Tenant.name.ilike(f"%{name.strip()}%"))

        total = q.count()

        rows = (
            q.order_by(Tenant.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for tenant, sub in rows:
            items.append(
                {
                    "tenant_id": tenant.id,
                    "name": tenant.name,
                    "created_at": tenant.created_at.isoformat() if getattr(tenant, "created_at", None) else None,
                    "subscription": {
                        "plan_type": getattr(sub, "plan_type", None),
                        "status": getattr(sub, "status", None),
                        "expires_at": sub.expires_at.isoformat() if getattr(sub, "expires_at", None) else None,
                        "case_limit": getattr(sub, "case_limit", None),
                        "active": getattr(sub, "active", None),
                    },
                }
            )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }

    except SQLAlchemyError as e:
        logger.exception("admin list tenants failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin list tenants failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin list tenants failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin list tenants failed: {type(e).__name__}: {e}")


@router.post("/tenants/{tenant_id}/subscription", dependencies=[Depends(require_admin_key)])
def upsert_subscription(
    tenant_id: int,
    payload: SubscriptionUpsertIn,
    db: Session = Depends(get_db),
):
    try:
        # RLS: opera “como” o tenant alvo
        set_tenant_on_session(db, tenant_id)

        # valida plan_type
        try:
            pt = PlanType(payload.plan_type)
        except Exception:
            raise HTTPException(status_code=422, detail="plan_type inválido (use basic|pro|office).")

        # valida status
        if payload.status not in ("trial", "active", "canceled"):
            raise HTTPException(status_code=422, detail="status inválido (use trial|active|canceled).")

        # normaliza expires_at -> UTC aware
        exp = payload.expires_at
        if exp is not None and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        sub = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .one_or_none()
        )

        lim = limits_for(pt)

        if sub is None:
            sub = Subscription(
                tenant_id=tenant_id,
                plan_type=getattr(pt, "value", str(pt)),
                status=payload.status,
                case_limit=lim.cases_per_month,
                active=payload.status in ("trial", "active"),
                expires_at=exp,
            )
            db.add(sub)
        else:
            sub.plan_type = getattr(pt, "value", str(pt))
            sub.status = payload.status
            sub.case_limit = lim.cases_per_month
            sub.active = payload.status in ("trial", "active")
            sub.expires_at = exp

        db.commit()
        db.refresh(sub)

        return {
            "tenant_id": tenant_id,
            "subscription": {
                "plan_type": sub.plan_type,
                "status": sub.status,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            },
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin upsert failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin upsert failed: SQLAlchemyError: {e}")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin upsert failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin upsert failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)


@router.get("/tenants/{tenant_id}/subscription", dependencies=[Depends(require_admin_key)])
def admin_get_subscription(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    try:
        sub = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .one_or_none()
        )
        if sub is None:
            raise HTTPException(status_code=404, detail="Subscription não encontrada.")

        return {
            "tenant_id": tenant_id,
            "subscription": {
                "plan_type": sub.plan_type,
                "status": sub.status,
                "active": bool(sub.active),
                "case_limit": sub.case_limit,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
                "created_at": sub.created_at.isoformat() if getattr(sub, "created_at", None) else None,
            },
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin get subscription failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin get subscription failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin get subscription failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin get subscription failed: {type(e).__name__}: {e}")


@router.patch("/tenants/{tenant_id}/subscription/active", dependencies=[Depends(require_admin_key)])
def toggle_subscription_active(
    tenant_id: int,
    payload: SubscriptionActiveToggleIn,
    db: Session = Depends(get_db),
):
    try:
        sub = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .one_or_none()
        )
        if sub is None:
            raise HTTPException(status_code=404, detail="Subscription não encontrada.")

        sub.active = payload.active
        sub.status = "active" if payload.active else "canceled"

        db.commit()
        db.refresh(sub)

        return {
            "tenant_id": tenant_id,
            "subscription": {
                "plan_type": sub.plan_type,
                "status": sub.status,
                "active": bool(sub.active),
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            },
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin toggle subscription failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin toggle subscription failed: SQLAlchemyError: {e}")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("admin toggle subscription failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin toggle subscription failed: {type(e).__name__}: {e}")


@router.get("/tenants/{tenant_id}/usage/summary", dependencies=[Depends(require_admin_key)])
def admin_usage_summary(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    month = date.today().replace(day=1)

    try:
        # RLS: opera “como” o tenant alvo
        set_tenant_on_session(db, tenant_id)

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

        return {
            "tenant_id": tenant_id,
            "month": month.isoformat(),
            "plan": {"type": getattr(eff.plan_type, "value", str(eff.plan_type)), "status": str(eff.status)},
            "limits": {
                "cases_per_month": lim.cases_per_month,
                "ai_analyses_per_month": lim.ai_analyses_per_month,
            },
            "used": {"cases_created": used_cases, "ai_analyses_generated": used_ai},
            "remaining": {"cases": remaining_cases, "ai_analyses": remaining_ai},
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin usage summary failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin usage summary failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin usage summary failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin usage summary failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)


@router.get("/tenants/{tenant_id}/usage/export", dependencies=[Depends(require_admin_key)])
def admin_usage_export(
    tenant_id: int,
    month: Optional[date] = Query(default=None, description="Primeiro dia do mês, ex: 2026-02-01"),
    format: str = Query(default="json", description="json|csv"),
    db: Session = Depends(get_db),
):
    m = month or date.today().replace(day=1)
    if m.day != 1:
        raise HTTPException(status_code=422, detail="month deve ser o primeiro dia do mês (YYYY-MM-01).")

    fmt = (format or "json").strip().lower()
    if fmt not in ("json", "csv"):
        raise HTTPException(status_code=422, detail="format inválido (use json|csv).")

    try:
        set_tenant_on_session(db, tenant_id)

        eff = get_effective_plan(db, tenant_id)
        lim = limits_for(eff.plan_type)

        row = (
            db.query(UsageCounter)
            .filter(UsageCounter.tenant_id == tenant_id, UsageCounter.month == m)
            .one_or_none()
        )

        used_cases = int(getattr(row, "cases_created", 0) or 0)
        used_ai = int(getattr(row, "ai_analyses_generated", 0) or 0)

        remaining_cases = max(lim.cases_per_month - used_cases, 0)
        remaining_ai = max(lim.ai_analyses_per_month - used_ai, 0)

        payload = {
            "tenant_id": tenant_id,
            "month": m.isoformat(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "plan": {"type": getattr(eff.plan_type, "value", str(eff.plan_type)), "status": str(eff.status)},
            "limits": {
                "cases_per_month": lim.cases_per_month,
                "ai_analyses_per_month": lim.ai_analyses_per_month,
            },
            "used": {"cases_created": used_cases, "ai_analyses_generated": used_ai},
            "remaining": {"cases": remaining_cases, "ai_analyses": remaining_ai},
        }

        if fmt == "json":
            return payload

        # CSV
        buf = io.StringIO()
        w = csv.writer(buf)

        header = [
            "tenant_id",
            "month",
            "exported_at",
            "plan_type",
            "plan_status",
            "limits_cases_per_month",
            "limits_ai_analyses_per_month",
            "used_cases_created",
            "used_ai_analyses_generated",
            "remaining_cases",
            "remaining_ai_analyses",
        ]
        w.writerow(header)
        w.writerow(
            [
                tenant_id,
                m.isoformat(),
                payload["exported_at"],
                payload["plan"]["type"],
                payload["plan"]["status"],
                payload["limits"]["cases_per_month"],
                payload["limits"]["ai_analyses_per_month"],
                payload["used"]["cases_created"],
                payload["used"]["ai_analyses_generated"],
                payload["remaining"]["cases"],
                payload["remaining"]["ai_analyses"],
            ]
        )

        filename = f"tenant-{tenant_id}-usage-{m.isoformat()}.csv"
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin usage export failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin usage export failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin usage export failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin usage export failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)



@router.get("/tenants/{tenant_id}/users", dependencies=[Depends(require_admin_key)])
def admin_list_tenant_users(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Lista usuários vinculados a um tenant específico.
    Visão global de backoffice/admin.
    """
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant não encontrado.")

        rows = (
            db.query(User, TenantMember)
            .join(TenantMember, TenantMember.user_id == User.id)
            .filter(TenantMember.tenant_id == tenant_id)
            .order_by(User.id.asc())
            .all()
        )

        items = [
            {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "tenant_role": member.role,
                "is_active": bool(user.is_active),
                "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
            }
            for user, member in rows
        ]

        return {
            "tenant_id": tenant_id,
            "count": len(items),
            "items": items,
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin list tenant users failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin list tenant users failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin list tenant users failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin list tenant users failed: {type(e).__name__}: {e}")



@router.get("/tenants/{tenant_id}", dependencies=[Depends(require_admin_key)])
def admin_get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Confirmação por ID (suporte): NÃO lista tenants.
    RLS-safe: opera como o tenant alvo.
    """
    try:
        set_tenant_on_session(db, tenant_id)

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant não encontrado.")

        eff = get_effective_plan(db, tenant_id)

        return {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "created_at": tenant.created_at.isoformat() if getattr(tenant, "created_at", None) else None,
            "plan": {
                "type": getattr(eff.plan_type, "value", str(eff.plan_type)),
                "status": str(eff.status),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin get tenant failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin get tenant failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)

@router.get("/tenants/{tenant_id}/usage/full", dependencies=[Depends(require_admin_key)])
def admin_tenant_usage_full(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Visão consolidada do tenant para backoffice/admin.
    Junta tenant, subscription, users e usage summary atual.
    """
    month = date.today().replace(day=1)

    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant não encontrado.")

        sub = (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .one_or_none()
        )

        user_rows = (
            db.query(User, TenantMember)
            .join(TenantMember, TenantMember.user_id == User.id)
            .filter(TenantMember.tenant_id == tenant_id)
            .order_by(User.id.asc())
            .all()
        )

        users_items = [
            {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "tenant_role": member.role,
                "is_active": bool(user.is_active),
                "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
            }
            for user, member in user_rows
        ]

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

        return {
            "tenant": {
                "tenant_id": tenant.id,
                "name": tenant.name,
                "created_at": tenant.created_at.isoformat() if getattr(tenant, "created_at", None) else None,
            },
            "subscription": {
                "plan_type": getattr(sub, "plan_type", None),
                "status": getattr(sub, "status", None),
                "active": getattr(sub, "active", None),
                "case_limit": getattr(sub, "case_limit", None),
                "expires_at": sub.expires_at.isoformat() if getattr(sub, "expires_at", None) else None,
                "created_at": sub.created_at.isoformat() if getattr(sub, "created_at", None) else None,
            } if sub else None,
            "users": {
                "count": len(users_items),
                "items": users_items,
            },
            "usage_summary": {
                "month": month.isoformat(),
                "plan": {
                    "type": getattr(eff.plan_type, "value", str(eff.plan_type)),
                    "status": str(eff.status),
                },
                "limits": {
                    "cases_per_month": lim.cases_per_month,
                    "ai_analyses_per_month": lim.ai_analyses_per_month,
                },
                "used": {
                    "cases_created": used_cases,
                    "ai_analyses_generated": used_ai,
                },
                "remaining": {
                    "cases": remaining_cases,
                    "ai_analyses": remaining_ai,
                },
            },
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin tenant usage full failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin tenant usage full failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin tenant usage full failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin tenant usage full failed: {type(e).__name__}: {e}")


@router.get("/tenants/{tenant_id}/usage/events", dependencies=[Depends(require_admin_key)])
def admin_usage_events(
    tenant_id: int,
    from_date: Optional[date] = Query(default=None, alias="from", description="YYYY-MM-DD (início)"),
    to_date: Optional[date] = Query(default=None, alias="to", description="YYYY-MM-DD (fim)"),
    limit: int = Query(default=200, ge=1, le=500, description="1..500"),
    db: Session = Depends(get_db),
):
    """
    Auditoria detalhada por tenant (suporte).
    NÃO lista tenants. Escopo 100% por tenant_id. RLS-safe.
    """
    today = date.today()
    fd = from_date or (today - timedelta(days=30))
    td = to_date or today

    if fd > td:
        raise HTTPException(status_code=422, detail="from deve ser <= to.")

    start_dt = datetime.combine(fd, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(td + timedelta(days=1), time.min, tzinfo=timezone.utc)  # exclusivo

    try:
        set_tenant_on_session(db, tenant_id)

        # Confirma tenant existe (evita retorno vazio por ID errado)
        t = db.query(Tenant).filter(Tenant.id == tenant_id).one_or_none()
        if t is None:
            raise HTTPException(status_code=404, detail="Tenant não encontrado.")

        q = (
            db.query(TenantUsageEvent)
            .filter(
                TenantUsageEvent.tenant_id == tenant_id,
                TenantUsageEvent.created_at >= start_dt,
                TenantUsageEvent.created_at < end_dt,
            )
            .order_by(TenantUsageEvent.created_at.desc(), TenantUsageEvent.id.desc())
            .limit(limit)
        )

        events = [
            {
                "id": e.id,
                "event_type": e.event_type,
                "resource_id": e.resource_id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in q.all()
        ]

        return {
            "tenant_id": tenant_id,
            "from": fd.isoformat(),
            "to": td.isoformat(),
            "limit": limit,
            "count": len(events),
            "events": events,
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.exception("admin usage events failed (SQLAlchemyError)")
        raise HTTPException(status_code=500, detail=f"admin usage events failed: SQLAlchemyError: {e}")
    except Exception as e:
        logger.exception("admin usage events failed (unexpected)")
        raise HTTPException(status_code=500, detail=f"admin usage events failed: {type(e).__name__}: {e}")
    finally:
        _reset_tenant_context(db)

