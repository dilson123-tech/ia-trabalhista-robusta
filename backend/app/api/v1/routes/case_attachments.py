from __future__ import annotations

import os
import re
import shutil
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import require_auth, require_role
from app.core.settings import settings
from app.core.tenant import scoped_query
from app.db.session import get_db
from app.models import Case, CaseAttachment
from app.schemas.case_attachment import CaseAttachmentOut, CaseAttachmentUpdate


router = APIRouter(
    prefix="/cases/{case_id}/attachments",
    tags=["case-attachments"],
)


_ALLOWED_CATEGORIES = {
    "foto",
    "video",
    "pdf",
    "documento_medico",
    "notificacao",
    "documento_pessoal",
    "contrato",
    "testemunha",
    "outro",
}


def _get_case_or_404(db: Session, current_user, case_id: int) -> Case:
    case = scoped_query(db, Case, current_user).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _safe_filename(filename: str) -> str:
    name = Path(filename or "arquivo").name.strip()
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name)
    name = re.sub(r"\s+", "_", name)
    return name[:180] or "arquivo"


def _case_upload_dir(tenant_id: int, case_id: int) -> Path:
    base_dir = Path(settings.CASE_ATTACHMENT_STORAGE_DIR)
    return base_dir / f"tenant_{tenant_id}" / f"case_{case_id}"


@router.get(
    "",
    response_model=list[CaseAttachmentOut],
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def list_case_attachments(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    return (
        db.query(CaseAttachment)
        .filter(
            CaseAttachment.tenant_id == current_user["tenant_id"],
            CaseAttachment.case_id == case_id,
        )
        .order_by(CaseAttachment.created_at.desc())
        .all()
    )


@router.post(
    "",
    response_model=CaseAttachmentOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def upload_case_attachment(
    case_id: int,
    file: UploadFile = File(...),
    category: str = Form("outro"),
    description: str | None = Form(None),
    event_date: date | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    case = _get_case_or_404(db, current_user, case_id)

    normalized_category = (category or "outro").strip().lower()
    if normalized_category not in _ALLOWED_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid attachment category")

    original_filename = _safe_filename(file.filename or "arquivo")
    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid.uuid4().hex}{suffix}"

    upload_dir = _case_upload_dir(current_user["tenant_id"], case.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    target_path = upload_dir / stored_filename

    size = 0
    try:
        with target_path.open("wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                out.write(chunk)
    finally:
        file.file.close()

    record = CaseAttachment(
        tenant_id=current_user["tenant_id"],
        case_id=case.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=str(target_path),
        mime_type=file.content_type,
        file_size_bytes=size,
        category=normalized_category,
        description=description,
        event_date=event_date,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.patch(
    "/{attachment_id}",
    response_model=CaseAttachmentOut,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def update_case_attachment(
    case_id: int,
    attachment_id: int,
    payload: CaseAttachmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    attachment = (
        db.query(CaseAttachment)
        .filter(
            CaseAttachment.id == attachment_id,
            CaseAttachment.case_id == case_id,
            CaseAttachment.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if payload.category is not None:
        attachment.category = payload.category
    if payload.description is not None:
        attachment.description = payload.description
    if payload.event_date is not None:
        attachment.event_date = payload.event_date

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


@router.get(
    "/{attachment_id}/download",
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def download_case_attachment(
    case_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    attachment = (
        db.query(CaseAttachment)
        .filter(
            CaseAttachment.id == attachment_id,
            CaseAttachment.case_id == case_id,
            CaseAttachment.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = Path(attachment.storage_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file not found")

    return FileResponse(
        path=path,
        media_type=attachment.mime_type or "application/octet-stream",
        filename=attachment.original_filename,
    )


@router.delete(
    "/{attachment_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin", "advogado"))],
)
def delete_case_attachment(
    case_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    _get_case_or_404(db, current_user, case_id)

    attachment = (
        db.query(CaseAttachment)
        .filter(
            CaseAttachment.id == attachment_id,
            CaseAttachment.case_id == case_id,
            CaseAttachment.tenant_id == current_user["tenant_id"],
        )
        .first()
    )

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = Path(attachment.storage_path)

    db.delete(attachment)
    db.commit()

    try:
        if path.exists() and path.is_file():
            os.remove(path)
        case_dir = path.parent
        if case_dir.exists():
            shutil.rmtree(case_dir, ignore_errors=True) if not any(case_dir.iterdir()) else None
    except OSError:
        pass

    return None
