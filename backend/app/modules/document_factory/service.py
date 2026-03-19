from __future__ import annotations

from app.modules.document_factory.contracts import (
    EvidenceItem,
    FactItem,
    GroundItem,
    PartyData,
    PleadingDraft,
    RequestItem,
)
from app.modules.document_factory.intake import (
    PeticaoInicialTrabalhistaIntake,
    build_peticao_inicial_payload_from_intake,
)
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

    def build_peticao_inicial_trabalhista_from_intake(
        self,
        *,
        intake: PeticaoInicialTrabalhistaIntake,
        case_id: int | None = None,
        tenant_id: int | None = None,
        user_id: int | None = None,
    ) -> PleadingDraft:
        payload = build_peticao_inicial_payload_from_intake(intake)
        base_draft = self.build_pleading(
            area="trabalhista",
            pleading_type="peticao_inicial_trabalhista",
            case_id=case_id,
            tenant_id=tenant_id,
            user_id=user_id,
            payload=payload,
        )

        return PleadingDraft(
            area=base_draft.area,
            pleading_type=base_draft.pleading_type,
            title=base_draft.title,
            parties=[
                PartyData(
                    role="reclamante",
                    name=intake.reclamante.nome,
                    document_id=intake.reclamante.documento,
                    metadata={"qualificacao": intake.reclamante.qualificacao},
                ),
                PartyData(
                    role="reclamada",
                    name=intake.reclamada.nome,
                    document_id=intake.reclamada.documento,
                    metadata={"qualificacao": intake.reclamada.qualificacao},
                ),
            ],
            facts=[
                FactItem(title=item.titulo, description=item.descricao)
                for item in intake.fatos
            ],
            requests=[
                RequestItem(
                    title=item.titulo,
                    description=item.descricao,
                    legal_basis=item.fundamento_legal,
                )
                for item in intake.pedidos
            ],
            grounds=[
                GroundItem(
                    title=item.titulo,
                    description=item.descricao,
                    citations=[item.fundamento_legal] if item.fundamento_legal else [],
                )
                for item in intake.fundamentos
            ],
            evidences=[
                EvidenceItem(title=item.titulo, description=item.descricao)
                for item in intake.provas
            ],
            sections=base_draft.sections,
            metadata=base_draft.metadata,
        )
