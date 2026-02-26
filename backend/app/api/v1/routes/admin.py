from __future__ import annotations

import os
import logging
import csv
import io
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.plans import PlanType, limits_for
from app.core.tenant import set_tenant_on_session
from app.db.session import get_db
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.usage_counter import UsageCounter
from app.services.plan_enforcement import get_effective_plan

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    expected = os.getenv("ADMIN_API_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY não configurada no ambiente.")
    if not x_admin_key or x_admin_key.strip() != expected:
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


class SubscriptionUpsertIn(BaseModel):
    plan_type: str = Field(..., description="basic|pro|office")
    status: str = Field(..., description="trial|active|canceled")
    expires_at: Optional[datetime] = Field(default=None, description="ISO datetime (UTC recomendado)")


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

        if sub is None:
            sub = Subscription(
                tenant_id=tenant_id,
                plan_type=getattr(pt, "value", str(pt)),
                status=payload.status,
                expires_at=exp,
            )
            db.add(sub)
        else:
            sub.plan_type = getattr(pt, "value", str(pt))
            sub.status = payload.status
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

