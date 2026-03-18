from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PartyData:
    role: str
    name: str
    document_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FactItem:
    title: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RequestItem:
    title: str
    description: str
    legal_basis: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GroundItem:
    title: str
    description: str
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvidenceItem:
    title: str
    description: str
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PleadingDraft:
    area: str
    pleading_type: str
    title: str
    parties: list[PartyData] = field(default_factory=list)
    facts: list[FactItem] = field(default_factory=list)
    requests: list[RequestItem] = field(default_factory=list)
    grounds: list[GroundItem] = field(default_factory=list)
    evidences: list[EvidenceItem] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
