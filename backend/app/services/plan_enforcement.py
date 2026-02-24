from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.plans import PlanType, limits_for
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter


class PlanAction:
    CASE_CREATE = "cases.create"
    AI_ANALYSIS_CREATE = "case_analyses.create"


@dataclass(frozen=True)
class EffectivePlan:
    plan_type: PlanType
    status: str  # active/trial/canceled (string do banco)


def _month_start(dt: datetime | None = None) -> date:
    d = (dt or datetime.now(timezone.utc)).date()
    return date(d.year, d.month, 1)


def get_effective_plan(db: Session, tenant_id: int) -> EffectivePlan:
    now = datetime.now(timezone.utc)
    sub = (
        db.query(Subscription)
        .filter(Subscription.tenant_id == tenant_id)
        .one_or_none()
    )

    # Sem assinatura = cai no basic (trial implícito)
    if not sub:
        return EffectivePlan(plan_type=PlanType.basic, status="trial")

    # Expirou? cai no basic (e segue vida)
    if sub.expires_at is not None and sub.expires_at <= now:
        return EffectivePlan(plan_type=PlanType.basic, status=sub.status)

    try:
        pt = PlanType(sub.plan_type)
    except Exception:
        pt = PlanType.basic

    # canceled não bloqueia o app inteiro; ele só “desce o plano” na prática
    if sub.status == "canceled":
        return EffectivePlan(plan_type=PlanType.basic, status="canceled")

    return EffectivePlan(plan_type=pt, status=sub.status)


def _get_or_create_counter_locked(db: Session, tenant_id: int, month: date) -> UsageCounter:
    q = (
        db.query(UsageCounter)
        .filter(UsageCounter.tenant_id == tenant_id, UsageCounter.month == month)
        .with_for_update()
    )
    row = q.one_or_none()
    if row:
        return row

    # cria e re-busca com lock (padrão seguro)
    row = UsageCounter(tenant_id=tenant_id, month=month, cases_created=0, ai_analyses_generated=0)
    db.add(row)
    db.flush()  # garante PK e respeita transação do request
    return q.one()


def enforce_plan_limits(db: Session, tenant_id: int, action: str) -> None:
    eff = get_effective_plan(db, tenant_id)
    lim = limits_for(eff.plan_type)
    month = _month_start()

    counter = _get_or_create_counter_locked(db, tenant_id, month)

    if action == PlanAction.CASE_CREATE:
        if (counter.cases_created + 1) > lim.cases_per_month:
            raise HTTPException(status_code=402, detail="Limite do plano atingido. Faça upgrade.")
        counter.cases_created += 1
        db.flush()
        return

    if action == PlanAction.AI_ANALYSIS_CREATE:
        if (counter.ai_analyses_generated + 1) > lim.ai_analyses_per_month:
            raise HTTPException(status_code=402, detail="Limite do plano atingido. Faça upgrade.")
        counter.ai_analyses_generated += 1
        db.flush()
        return

    raise HTTPException(status_code=400, detail=f"Ação inválida de plano: {action}")
