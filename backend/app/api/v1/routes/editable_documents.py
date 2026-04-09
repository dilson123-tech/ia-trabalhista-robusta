from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case, User
from app.models.editable_document import EditableDocument, EditableDocumentVersion
from app.schemas.editable_document import (
    EditableDocumentCreate,
    EditableDocumentDetailOut,
    EditableDocumentOut,
    EditableDocumentVersionCreate,
    EditableDocumentVersionOut,
)
from app.services.editor_export_service import build_editor_html, generate_editor_pdf

router = APIRouter(
    prefix="/editable-documents",
    tags=["editable-documents"],
)


def _resolve_current_user_id(db: Session, current_user: dict) -> int | None:
    username = current_user.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user.id if user else None


def _build_document_detail_payload(
    db: Session,
    document: EditableDocument,
) -> dict:
    versions = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.tenant_id == document.tenant_id,
            EditableDocumentVersion.editable_document_id == document.id,
        )
        .order_by(EditableDocumentVersion.version_number.asc())
        .all()
    )

    return {
        "id": document.id,
        "tenant_id": document.tenant_id,
        "case_id": document.case_id,
        "created_by_user_id": document.created_by_user_id,
        "area": document.area,
        "document_type": document.document_type,
        "title": document.title,
        "status": document.status,
        "current_version_number": document.current_version_number,
        "document_metadata": document.document_metadata or {},
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "versions": [
            {
                "id": version.id,
                "editable_document_id": version.editable_document_id,
                "tenant_id": version.tenant_id,
                "version_number": version.version_number,
                "approved": version.approved,
                "notes": version.notes,
                "sections": version.sections or [],
                "version_metadata": version.version_metadata or {},
                "created_by_user_id": version.created_by_user_id,
                "created_at": version.created_at,
            }
            for version in versions
        ],
    }


@router.post(
    "",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_editable_document(
    payload: EditableDocumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == payload.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    current_user_id = _resolve_current_user_id(db, current_user)

    document = EditableDocument(
        tenant_id=current_user["tenant_id"],
        case_id=payload.case_id,
        created_by_user_id=current_user_id,
        area=payload.area,
        document_type=payload.document_type,
        title=payload.title,
        status="draft",
        current_version_number=1,
        document_metadata=payload.metadata,
    )
    db.add(document)
    db.flush()

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=1,
        approved=False,
        notes=payload.notes,
        sections=[section.model_dump() for section in payload.sections],
        version_metadata={
            **payload.metadata,
            "source": "api_create_editable_document",
        },
    )
    db.add(version)
    db.commit()
    db.refresh(document)

    return _build_document_detail_payload(db, document)


@router.get(
    "/case/{case_id}",
    response_model=list[EditableDocumentOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_editable_documents_for_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = (
        scoped_query(db, Case, current_user)
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return (
        db.query(EditableDocument)
        .filter(
            EditableDocument.tenant_id == current_user["tenant_id"],
            EditableDocument.case_id == case_id,
        )
        .order_by(EditableDocument.updated_at.desc())
        .all()
    )


@router.get(
    "/{document_id}",
    response_model=EditableDocumentDetailOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def get_editable_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    return _build_document_detail_payload(db, document)


@router.delete(
    "/{document_id}",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_editable_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    versions_count = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
        )
        .count()
    )

    db.delete(document)
    db.commit()

    return {
        "deleted_document_id": document_id,
        "deleted_versions_count": versions_count,
        "detail": "Editable document deleted successfully",
    }


@router.get(
    "/{document_id}/export/html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def export_editable_document_html(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    approved_version = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .first()
    )

    if not approved_version:
        raise HTTPException(
            status_code=409,
            detail="Editable document does not have an approved version for final export",
        )

    html = build_editor_html(
        {
            "title": document.title,
            "area": document.area,
            "document_type": document.document_type,
        },
        {
            "version_number": approved_version.version_number,
            "sections": approved_version.sections or [],
        },
    )

    return HTMLResponse(content=html)


@router.get(
    "/{document_id}/export/pdf",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def export_editable_document_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    approved_version = (
        db.query(EditableDocumentVersion)
        .filter(
            EditableDocumentVersion.editable_document_id == document.id,
            EditableDocumentVersion.tenant_id == current_user["tenant_id"],
            EditableDocumentVersion.approved.is_(True),
        )
        .order_by(EditableDocumentVersion.version_number.desc())
        .first()
    )

    if not approved_version:
        raise HTTPException(
            status_code=409,
            detail="Editable document does not have an approved version for final export",
        )

    html = build_editor_html(
        {
            "title": document.title,
            "area": document.area,
            "document_type": document.document_type,
        },
        {
            "version_number": approved_version.version_number,
            "sections": approved_version.sections or [],
        },
    )

    pdf_bytes = generate_editor_pdf(html)

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="editable_document_{document.id}_v{approved_version.version_number}.pdf"'
        },
    )


@router.post(
    "/{document_id}/versions",
    response_model=EditableDocumentVersionOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def create_editable_document_version(
    document_id: int,
    payload: EditableDocumentVersionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    document = (
        db.query(EditableDocument)
        .filter(
            EditableDocument.id == document_id,
            EditableDocument.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Editable document not found")

    current_user_id = _resolve_current_user_id(db, current_user)
    next_version_number = document.current_version_number + 1

    version = EditableDocumentVersion(
        tenant_id=current_user["tenant_id"],
        editable_document_id=document.id,
        created_by_user_id=current_user_id,
        version_number=next_version_number,
        approved=payload.approved,
        notes=payload.notes,
        sections=[section.model_dump() for section in payload.sections],
        version_metadata=payload.metadata,
    )
    db.add(version)

    document.current_version_number = next_version_number
    document.status = "approved" if payload.approved else "draft"
    db.add(document)

    db.commit()
    db.refresh(version)

    return version
