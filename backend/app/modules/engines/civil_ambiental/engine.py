from __future__ import annotations

from app.modules.engines.base import (
    EngineAnalysisResult,
    EngineContext,
    EnginePleadingResult,
)
from app.modules.engines.civil_ambiental.pleadings import (
    build_peticao_inicial_civil_sections,
)


class CivilAmbientalEngine:
    area = "civil_ambiental"

    def analyze_case(self, context: EngineContext) -> EngineAnalysisResult:
        case_title = context.payload.get("title") or "Caso cível"
        return EngineAnalysisResult(
            area=self.area,
            summary=f"Análise inicial da vertical cível para: {case_title}.",
            risk_level="medium",
            highlights=[
                "Engine cível conectada ao núcleo modular.",
                "Base pronta para peças iniciais e evolução de regras específicas da área.",
            ],
            recommendations=[
                "Consolidar fatos, documentos e cronologia do caso.",
                "Refinar pedidos, valor da causa e estratégia processual.",
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

        if normalized_type in {"peticao_inicial", "peticao_inicial_civil", "peticao_inicial_civel"}:
            sections = build_peticao_inicial_civil_sections(context.payload)
            title = "Petição Inicial Cível"
            structured_template = True
        else:
            sections = [
                {
                    "key": "fatos",
                    "title": "Dos fatos",
                    "content": "Estrutura inicial para fatos relevantes do caso cível.",
                },
                {
                    "key": "fundamentos",
                    "title": "Dos fundamentos jurídicos",
                    "content": "Estrutura inicial para a fundamentação jurídica da peça cível.",
                },
                {
                    "key": "pedidos",
                    "title": "Dos pedidos",
                    "content": "Estrutura inicial para organização objetiva dos pedidos.",
                },
            ]
            title = f"Minuta inicial — {pleading_type}"
            structured_template = False

        return EnginePleadingResult(
            area=self.area,
            pleading_type=pleading_type,
            title=title,
            sections=sections,
            metadata={
                "engine": self.area,
                "mode": "pleading_generation",
                "scaffold": True,
                "structured_template": structured_template,
            },
        )
