from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.document_factory.contracts import PleadingDraft


@dataclass(slots=True)
class EditableSection:
    key: str
    title: str
    content: str
    source: str = "ai"
    status: str = "draft"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentVersion:
    version: int
    sections: list[EditableSection] = field(default_factory=list)
    approved: bool = False
    created_by_user_id: int | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EditableDocument:
    area: str
    document_type: str
    title: str
    case_id: int | None = None
    tenant_id: int | None = None
    versions: list[DocumentVersion] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def current_version(self) -> DocumentVersion | None:
        return self.versions[-1] if self.versions else None


def build_editable_sections_from_draft(draft: PleadingDraft) -> list[EditableSection]:
    sections: list[EditableSection] = []

    for index, section in enumerate(draft.sections, start=1):
        sections.append(
            EditableSection(
                key=section.get("key") or f"section_{index}",
                title=section.get("title") or f"Seção {index}",
                content=section.get("content") or "",
                metadata={
                    "origin_index": index,
                    "draft_area": draft.area,
                    "draft_type": draft.pleading_type,
                },
            )
        )

    return sections


def build_editable_document_from_draft(
    draft: PleadingDraft,
    *,
    created_by_user_id: int | None = None,
) -> EditableDocument:
    sections = build_editable_sections_from_draft(draft)

    initial_version = DocumentVersion(
        version=1,
        sections=sections,
        approved=False,
        created_by_user_id=created_by_user_id,
        metadata={
            "draft_metadata": draft.metadata,
            "source": "initial_draft_import",
        },
    )

    return EditableDocument(
        area=draft.area,
        document_type=draft.pleading_type,
        title=draft.title,
        case_id=draft.metadata.get("case_id"),
        tenant_id=draft.metadata.get("tenant_id"),
        versions=[initial_version],
        metadata={
            "source": "document_factory",
        },
    )
