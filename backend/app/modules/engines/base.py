from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class EngineContext:
    area: str
    case_id: int | None = None
    tenant_id: int | None = None
    user_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EngineAnalysisResult:
    area: str
    summary: str
    risk_level: str
    highlights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EnginePleadingResult:
    area: str
    pleading_type: str
    title: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class LegalEngine(Protocol):
    area: str

    def analyze_case(self, context: EngineContext) -> EngineAnalysisResult:
        ...

    def generate_pleading(
        self,
        context: EngineContext,
        pleading_type: str,
    ) -> EnginePleadingResult:
        ...
