from __future__ import annotations

from app.modules.document_factory.contracts import PleadingDraft
from app.modules.engines.base import EngineContext
from app.modules.engines.registry import get_engine


class DocumentFactoryService:
    def build_pleading(
        self,
        *,
        area: str,
        pleading_type: str,
        case_id: int | None = None,
        tenant_id: int | None = None,
        user_id: int | None = None,
        payload: dict | None = None,
    ) -> PleadingDraft:
        context = EngineContext(
            area=area,
            case_id=case_id,
            tenant_id=tenant_id,
            user_id=user_id,
            payload=payload or {},
        )

        engine = get_engine(area)
        result = engine.generate_pleading(context, pleading_type)

        return PleadingDraft(
            area=result.area,
            pleading_type=result.pleading_type,
            title=result.title,
            sections=result.sections,
            metadata=result.metadata,
        )
