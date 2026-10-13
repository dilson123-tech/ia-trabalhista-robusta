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
from app.core.tenant import scoped_query, set_tenant_on_session
from app.db.session import get_db
from app.models import Case, CaseAttachment
from app.schemas.case_attachment import CaseAttachmentOut, CaseAttachmentUpdate
from app.services.attachment_content_validation import (
    AttachmentValidatorUnavailable,
    UnsupportedAttachmentContent,
    validate_attachment_content,
)


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


MAX_DOCUMENT_IMAGE_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_MEDIA_UPLOAD_BYTES = 100 * 1024 * 1024

_UPLOAD_CHUNK_BYTES = 1024 * 1024
_UNDECLARED_CONTENT_TYPES = {"", "application/octet-stream"}
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# extensão final → (mime canônico persistido, content_types declarados aceitos, limite em bytes)
_UPLOAD_FORMATS = {
    ".pdf": ("application/pdf", {"application/pdf"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".doc": ("application/msword", {"application/msword"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".docx": (_DOCX_MIME, {_DOCX_MIME}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".txt": ("text/plain", {"text/plain"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".jpg": ("image/jpeg", {"image/jpeg", "image/pjpeg"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".jpeg": ("image/jpeg", {"image/jpeg", "image/pjpeg"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".png": ("image/png", {"image/png"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".webp": ("image/webp", {"image/webp"}, MAX_DOCUMENT_IMAGE_UPLOAD_BYTES),
    ".mp3": ("audio/mpeg", {"audio/mpeg", "audio/mp3"}, MAX_MEDIA_UPLOAD_BYTES),
    ".wav": ("audio/wav", {"audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave"}, MAX_MEDIA_UPLOAD_BYTES),
    ".m4a": ("audio/mp4", {"audio/mp4", "audio/x-m4a", "audio/m4a"}, MAX_MEDIA_UPLOAD_BYTES),
    ".mp4": ("video/mp4", {"video/mp4", "application/mp4"}, MAX_MEDIA_UPLOAD_BYTES),
    ".mov": ("video/quicktime", {"video/quicktime"}, MAX_MEDIA_UPLOAD_BYTES),
    ".webm": ("video/webm", {"video/webm", "audio/webm"}, MAX_MEDIA_UPLOAD_BYTES),
}


def _unsupported_media(detail: str = "Unsupported attachment format") -> HTTPException:
    return HTTPException(status_code=415, detail=detail)


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
    try:
        return _store_case_attachment(
            case_id, file, category, description, event_date, db, current_user
        )
    finally:
        file.file.close()


def _store_case_attachment(
    case_id: int,
    file: UploadFile,
    category: str,
    description: str | None,
    event_date: date | None,
    db: Session,
    current_user,
) -> CaseAttachment:
    case = _get_case_or_404(db, current_user, case_id)

    normalized_category = (category or "outro").strip().lower()
    if normalized_category not in _ALLOWED_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid attachment category")

    original_filename = _safe_filename(file.filename or "arquivo")
    suffix = Path(original_filename).suffix.lower()
    upload_format = _UPLOAD_FORMATS.get(suffix)
    if upload_format is None:
        raise _unsupported_media()
    canonical_mime, accepted_content_types, max_bytes = upload_format

    declared_content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if (
        declared_content_type not in _UNDECLARED_CONTENT_TYPES
        and declared_content_type not in accepted_content_types
    ):
        raise _unsupported_media("Attachment content type does not match extension")

    stored_filename = f"{uuid.uuid4().hex}{suffix}"

    upload_dir = _case_upload_dir(current_user["tenant_id"], case.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    target_path = upload_dir / stored_filename

    size = 0
    try:
        with target_path.open("wb") as out:
            while True:
                chunk = file.file.read(_UPLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(status_code=413, detail="Attachment exceeds size limit")
                out.write(chunk)

        if size == 0:
            raise HTTPException(status_code=422, detail="Empty attachment")

        try:
            validate_attachment_content(target_path, suffix)
        except UnsupportedAttachmentContent as exc:
            raise _unsupported_media(str(exc)) from exc
        except AttachmentValidatorUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        record = CaseAttachment(
            tenant_id=current_user["tenant_id"],
            case_id=case.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=str(target_path),
            mime_type=canonical_mime,
            file_size_bytes=size,
            category=normalized_category,
            description=description,
            event_date=event_date,
        )

        # flush/refresh antes do commit: nenhuma operação de banco após o commit
        # (expire_on_commit=False), então qualquer falha até aqui limpa arquivo e transação.
        db.add(record)
        db.flush()
        db.refresh(record)
    except Exception:
        target_path.unlink(missing_ok=True)
        db.rollback()
        raise

    try:
        db.commit()
    except Exception:
        # commit ambíguo: a exceção não prova que nada foi persistido (ex.: conexão
        # perdida após o COMMIT chegar ao banco). Só remove o arquivo se uma nova
        # sessão confirmar que o registro não existe; na dúvida, preserva o arquivo.
        try:
            db.rollback()
        except Exception:
            pass
        if _attachment_record_absent(db, current_user["tenant_id"], target_path):
            target_path.unlink(missing_ok=True)
        raise

    return record


def _attachment_record_absent(db: Session, tenant_id: int, target_path: Path) -> bool:
    """True somente se uma sessão nova confirmar a ausência do registro do arquivo."""
    try:
        reconcile = Session(bind=db.get_bind(), autoflush=False, expire_on_commit=False)
    except Exception:
        return False
    try:
        set_tenant_on_session(reconcile, tenant_id)
        existing_id = (
            reconcile.query(CaseAttachment.id)
            .filter(
                CaseAttachment.tenant_id == tenant_id,
                CaseAttachment.storage_path == str(target_path),
            )
            .first()
        )
        return existing_id is None
    except Exception:
        return False
    finally:
        try:
            reconcile.close()
        except Exception:
            pass


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
