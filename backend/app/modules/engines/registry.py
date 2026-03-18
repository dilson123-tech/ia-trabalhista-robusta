from __future__ import annotations

from app.modules.engines.trabalhista import TrabalhistaEngine


_ENGINE_REGISTRY = {
    "trabalhista": TrabalhistaEngine,
}


def get_engine(area: str):
    normalized = (area or "").strip().lower()
    engine_cls = _ENGINE_REGISTRY.get(normalized)
    if not engine_cls:
        available = ", ".join(sorted(_ENGINE_REGISTRY.keys())) or "nenhuma"
        raise ValueError(
            f"Área jurídica não suportada: '{area}'. Áreas disponíveis: {available}."
        )
    return engine_cls()


def list_engines() -> list[str]:
    return sorted(_ENGINE_REGISTRY.keys())
