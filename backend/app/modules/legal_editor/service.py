from __future__ import annotations

from app.modules.document_factory.contracts import PleadingDraft
from app.modules.legal_editor.contracts import (
    DocumentVersion,
    EditableDocument,
    EditableSection,
    build_editable_document_from_draft,
)


class LegalEditorService:
    def create_from_draft(
        self,
        *,
        draft: PleadingDraft,
        created_by_user_id: int | None = None,
    ) -> EditableDocument:
        return build_editable_document_from_draft(
            draft,
            created_by_user_id=created_by_user_id,
        )

    def update_section(
        self,
        *,
        document: EditableDocument,
        section_key: str,
        new_content: str,
        edited_by_user_id: int | None = None,
        notes: str | None = None,
    ) -> EditableDocument:
        current_version = document.current_version
        if current_version is None:
            raise ValueError("editable document has no current version")

        updated = False
        cloned_sections: list[EditableSection] = []

        for section in current_version.sections:
            cloned = EditableSection(
                key=section.key,
                title=section.title,
                content=section.content,
                source=section.source,
                status=section.status,
                metadata=dict(section.metadata),
            )

            if section.key == section_key:
                cloned.content = new_content
                cloned.source = "manual"
                cloned.status = "edited"
                cloned.metadata["edited_by_user_id"] = edited_by_user_id
                updated = True

            cloned_sections.append(cloned)

        if not updated:
            raise ValueError(f"section '{section_key}' not found")

        new_version = DocumentVersion(
            version=current_version.version + 1,
            sections=cloned_sections,
            approved=False,
            created_by_user_id=edited_by_user_id,
            notes=notes,
            metadata={
                "parent_version": current_version.version,
                "change_type": "section_update",
                "section_key": section_key,
            },
        )

        return EditableDocument(
            area=document.area,
            document_type=document.document_type,
            title=document.title,
            case_id=document.case_id,
            tenant_id=document.tenant_id,
            versions=[*document.versions, new_version],
            metadata=dict(document.metadata),
        )

    def approve_current_version(
        self,
        *,
        document: EditableDocument,
        approved_by_user_id: int | None = None,
        notes: str | None = None,
    ) -> EditableDocument:
        current_version = document.current_version
        if current_version is None:
            raise ValueError("editable document has no current version")

        approved_sections = [
            EditableSection(
                key=section.key,
                title=section.title,
                content=section.content,
                source=section.source,
                status="approved",
                metadata=dict(section.metadata),
            )
            for section in current_version.sections
        ]

        approved_version = DocumentVersion(
            version=current_version.version + 1,
            sections=approved_sections,
            approved=True,
            created_by_user_id=approved_by_user_id,
            notes=notes,
            metadata={
                "parent_version": current_version.version,
                "change_type": "approval",
                "approved_by_user_id": approved_by_user_id,
            },
        )

        return EditableDocument(
            area=document.area,
            document_type=document.document_type,
            title=document.title,
            case_id=document.case_id,
            tenant_id=document.tenant_id,
            versions=[*document.versions, approved_version],
            metadata=dict(document.metadata),
        )
