from __future__ import annotations

import enum
import os
from dataclasses import dataclass


class PlanType(str, enum.Enum):
    basic = "basic"
    pro = "pro"
    office = "office"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    trial = "trial"
    canceled = "canceled"


@dataclass(frozen=True)
class PlanLimits:
    cases_per_month: int
    ai_analyses_per_month: int


# Fonte da verdade (pode tunar via env sem mexer em código — ótimo pra testes/CI)
LIMITS: dict[PlanType, PlanLimits] = {
    PlanType.basic: PlanLimits(
        cases_per_month=int(os.getenv("PLAN_BASIC_CASES_PER_MONTH", "50")),
        ai_analyses_per_month=int(os.getenv("PLAN_BASIC_AI_ANALYSES_PER_MONTH", "20")),
    ),
    PlanType.pro: PlanLimits(
        cases_per_month=int(os.getenv("PLAN_PRO_CASES_PER_MONTH", "200")),
        ai_analyses_per_month=int(os.getenv("PLAN_PRO_AI_ANALYSES_PER_MONTH", "100")),
    ),
    PlanType.office: PlanLimits(
        cases_per_month=int(os.getenv("PLAN_OFFICE_CASES_PER_MONTH", "1000")),
        ai_analyses_per_month=int(os.getenv("PLAN_OFFICE_AI_ANALYSES_PER_MONTH", "500")),
    ),
}


def limits_for(plan_type: PlanType | str | None) -> PlanLimits:
    try:
        pt = plan_type if isinstance(plan_type, PlanType) else PlanType(str(plan_type))
    except Exception:
        pt = PlanType.basic
    return LIMITS.get(pt, LIMITS[PlanType.basic])
