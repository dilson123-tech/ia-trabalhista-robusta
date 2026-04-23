from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.plans import PlanType, limits_for
from app.models.case import Case
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter


class PlanAction:
    CASE_CREATE = "cases.create"
    CASE_RESTORE = "cases.restore"
    AI_ANALYSIS_CREATE = "case_analyses.create"


@dataclass(frozen=True)
class EffectivePlan:
    plan_type: PlanType
    status: str  # active/trial/canceled (string do banco)


@dataclass(frozen=True)
class CaseCapacitySummary:
    active_cases: int
    archived_cases: int
    case_records: int
    active_cases_limit: int
    case_records_limit: int
    remaining_active_cases: int
    remaining_case_records: int


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

    if not sub:
        return EffectivePlan(plan_type=PlanType.basic, status="trial")

    exp = sub.expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp is not None and exp <= now:
        return EffectivePlan(plan_type=PlanType.basic, status=sub.status)

    try:
        pt = PlanType(sub.plan_type)
    except Exception:
        pt = PlanType.basic

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

    row = UsageCounter(tenant_id=tenant_id, month=month, cases_created=0, ai_analyses_generated=0)
    db.add(row)
    db.flush()
    return q.one()


def _active_case_filter():
    return or_(Case.status.is_(None), Case.status != "archived")


def _count_active_cases(db: Session, tenant_id: int) -> int:
    return (
        db.query(Case)
        .filter(Case.tenant_id == tenant_id)
        .filter(_active_case_filter())
        .count()
    )


def _count_case_records(db: Session, tenant_id: int) -> int:
    return db.query(Case).filter(Case.tenant_id == tenant_id).count()


def get_case_capacity_summary(db: Session, tenant_id: int) -> CaseCapacitySummary:
    eff = get_effective_plan(db, tenant_id)
    lim = limits_for(eff.plan_type)

    active_cases = _count_active_cases(db, tenant_id)
    case_records = _count_case_records(db, tenant_id)
    archived_cases = max(case_records - active_cases, 0)

    return CaseCapacitySummary(
        active_cases=active_cases,
        archived_cases=archived_cases,
        case_records=case_records,
        active_cases_limit=lim.active_cases_limit,
        case_records_limit=lim.case_records_limit,
        remaining_active_cases=max(lim.active_cases_limit - active_cases, 0),
        remaining_case_records=max(lim.case_records_limit - case_records, 0),
    )


def _enforce_case_storage_limits(
    db: Session,
    tenant_id: int,
    *,
    extra_active: int,
    extra_records: int,
) -> None:
    storage = get_case_capacity_summary(db, tenant_id)

    if (storage.case_records + extra_records) > storage.case_records_limit:
        raise HTTPException(
            status_code=402,
            detail="Limite de acervo do plano atingido. Faça upgrade para armazenar mais casos.",
        )

    if (storage.active_cases + extra_active) > storage.active_cases_limit:
        raise HTTPException(
            status_code=402,
            detail="Limite de casos ativos do plano atingido. Arquive um caso ou faça upgrade.",
        )


def enforce_plan_limits(db: Session, tenant_id: int, action: str) -> None:
    eff = get_effective_plan(db, tenant_id)
    lim = limits_for(eff.plan_type)
    month = _month_start()

    counter = _get_or_create_counter_locked(db, tenant_id, month)

    if action == PlanAction.CASE_CREATE:
        _enforce_case_storage_limits(db, tenant_id, extra_active=1, extra_records=1)
        counter.cases_created += 1
        db.flush()
        return

    if action == PlanAction.CASE_RESTORE:
        _enforce_case_storage_limits(db, tenant_id, extra_active=1, extra_records=0)
        db.flush()
        return

    if action == PlanAction.AI_ANALYSIS_CREATE:
        if (counter.ai_analyses_generated + 1) > lim.ai_analyses_per_month:
            raise HTTPException(status_code=402, detail="Limite do plano atingido. Faça upgrade.")
        counter.ai_analyses_generated += 1
        db.flush()
        return

    raise HTTPException(status_code=400, detail=f"Ação inválida de plano: {action}")
