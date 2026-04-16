from __future__ import annotations

import enum
from dataclasses import dataclass

from app.core.settings import settings


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
    active_cases_limit: int
    case_records_limit: int
    ai_analyses_per_month: int

    @property
    def cases_per_month(self) -> int:
        # alias legado para não quebrar contratos antigos imediatamente
        return self.active_cases_limit


LIMITS: dict[PlanType, PlanLimits] = {
    PlanType.basic: PlanLimits(
        active_cases_limit=settings.PLAN_BASIC_ACTIVE_CASES_LIMIT,
        case_records_limit=settings.PLAN_BASIC_CASE_RECORDS_LIMIT,
        ai_analyses_per_month=settings.PLAN_BASIC_AI_ANALYSES_PER_MONTH,
    ),
    PlanType.pro: PlanLimits(
        active_cases_limit=settings.PLAN_PRO_ACTIVE_CASES_LIMIT,
        case_records_limit=settings.PLAN_PRO_CASE_RECORDS_LIMIT,
        ai_analyses_per_month=settings.PLAN_PRO_AI_ANALYSES_PER_MONTH,
    ),
    PlanType.office: PlanLimits(
        active_cases_limit=settings.PLAN_OFFICE_ACTIVE_CASES_LIMIT,
        case_records_limit=settings.PLAN_OFFICE_CASE_RECORDS_LIMIT,
        ai_analyses_per_month=settings.PLAN_OFFICE_AI_ANALYSES_PER_MONTH,
    ),
}


def limits_for(plan_type: PlanType | str | None) -> PlanLimits:
    try:
        pt = plan_type if isinstance(plan_type, PlanType) else PlanType(str(plan_type))
    except Exception:
        pt = PlanType.basic
    return LIMITS.get(pt, LIMITS[PlanType.basic])
