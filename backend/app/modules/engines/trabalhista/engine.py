from __future__ import annotations

from app.modules.engines.base import (
    EngineAnalysisResult,
    EngineContext,
    EnginePleadingResult,
)
from app.modules.engines.trabalhista.pleadings import (
    build_peticao_inicial_trabalhista_sections,
)


class TrabalhistaEngine:
    area = "trabalhista"

    def analyze_case(self, context: EngineContext) -> EngineAnalysisResult:
        case_title = context.payload.get("title") or "Caso trabalhista"
        return EngineAnalysisResult(
            area=self.area,
            summary=f"Análise inicial da vertical trabalhista para: {case_title}.",
            risk_level="medium",
            highlights=[
                "Engine trabalhista conectada ao núcleo modular.",
                "Ponto de extensão pronto para regras específicas da área.",
            ],
            recommendations=[
                "Mapear fatos relevantes do vínculo.",
                "Identificar pedidos e fundamentos aplicáveis.",
            ],
            metadata={
                "engine": self.area,
                "mode": "analysis",
                "scaffold": True,
            },
        )

    def generate_pleading(
        self,
        context: EngineContext,
        pleading_type: str,
    ) -> EnginePleadingResult:
        normalized_type = (pleading_type or "").strip().lower()

        if normalized_type == "peticao_inicial_trabalhista":
            sections = build_peticao_inicial_trabalhista_sections(context.payload)
            title = "Petição Inicial Trabalhista"
        else:
            sections = [
                {
                    "key": "fatos",
                    "title": "Dos fatos",
                    "content": "Estrutura inicial para fatos relevantes do caso trabalhista.",
                },
                {
                    "key": "fundamentos",
                    "title": "Dos fundamentos",
                    "content": "Estrutura inicial para fundamentos jurídicos da peça.",
                },
                {
                    "key": "pedidos",
                    "title": "Dos pedidos",
                    "content": "Estrutura inicial para organização dos pedidos.",
                },
            ]
            title = f"Minuta inicial — {pleading_type}"

        return EnginePleadingResult(
            area=self.area,
            pleading_type=pleading_type,
            title=title,
            sections=sections,
            metadata={
                "engine": self.area,
                "mode": "pleading_generation",
                "scaffold": True,
                "structured_template": normalized_type == "peticao_inicial_trabalhista",
            },
        )
