"""Política de upload de anexos de caso (Missão 005 / F4, Arquitetura A).

Valida, pelo endpoint real `POST /api/v1/cases/{case_id}/attachments`:

- whitelist de formatos por extensão final (case-insensitive);
- coerência entre extensão e content_type declarado;
- validação estrutural do conteúdo pelo parser especializado de cada formato
  (pypdf, olefile, zipfile + defusedxml, UTF-8, Pillow, ffprobe);
- limites por classe aplicados durante a leitura em chunks:
  documentos/imagens 26214400 bytes, áudio/vídeo 104857600 bytes;
- 0 bytes e categoria inválida → 422; formato/conteúdo/política → 415;
  tamanho → 413; validador de mídia indisponível → 503;
- mime_type persistido canônico, derivado pelo servidor;
- nenhum registro nem arquivo parcial após rejeição ou falha de
  flush/refresh/commit; UploadFile fechado em todos os caminhos;
- RBAC (admin/advogado) e isolamento de tenant preservados.

Amostras são arquivos válidos gerados em memória (pypdf, Pillow, zipfile) ou
por ffmpeg real (mídia; testes pulados se ffmpeg/ffprobe ausentes). Fixtures
binárias versionadas: `fixtures/plain_word97.doc` (Word 97 real, sem VBA) e
`fixtures/poi_SimpleMacro.doc` (DOC real com projeto VBA, copiado do
test-data do Apache POI, Apache-2.0; procedência registrada no teste).

O armazenamento aponta para `tmp_path` via monkeypatch; nenhum .env, segredo
real ou banco real é usado.
"""

import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import uuid
import warnings
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy import text

from app.api.v1.routes import case_attachments
from app.core.security import pwd_context
from app.core.settings import settings
from app.core.tenant import set_tenant_on_session
from app.models import Case, CaseAttachment
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.services import attachment_content_validation as acv

DOC_IMAGE_LIMIT = 26214400
MEDIA_LIMIT = 104857600

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLAIN_DOC_FIXTURE = FIXTURES_DIR / "plain_word97.doc"
# Apache POI test-data/document/SimpleMacro.doc (bug 52949), commit
# e3ad497b79b0135659c6b6d1c011e3fbabb91a14, Apache-2.0. DOC real com storage Macros/VBA.
VBA_DOC_FIXTURE = FIXTURES_DIR / "poi_SimpleMacro.doc"
VBA_DOC_SHA256 = "39e9608c711d38f298ed20a5bfae12fcdaed6f4be2be4d26db670475216ca393"

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
requires_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg/ffprobe indisponível no ambiente")

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_DOCX_MAIN = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ---------------------------------------------------------------------------
# Amostras válidas por formato
# ---------------------------------------------------------------------------

def _pdf_bytes():
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _encrypted_pdf_bytes():
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt("senha")
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _content_types_xml(main_content_type=_DOCX_MAIN, extra=""):
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/word/document.xml" ContentType="{main_content_type}"/>'
        f"{extra}"
        "</Types>"
    )


_RELS_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    "</Relationships>"
)

_DOCUMENT_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:document xmlns:w="{_W_NS}"><w:body><w:p><w:r>'
    "<w:t>Relato do reclamante.</w:t>"
    "</w:r></w:p></w:body></w:document>"
)


def _docx_bytes(content_types=None, document=_DOCUMENT_XML, extra_entries=(), rels=_RELS_XML):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types if content_types is not None else _content_types_xml())
        if rels is not None:
            zf.writestr("_rels/.rels", rels)
        if document is not None:
            zf.writestr("word/document.xml", document)
        for name, data in extra_entries:
            zf.writestr(name, data)
    return buf.getvalue()


def _image_bytes(fmt):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 30, 30)).save(buf, format=fmt)
    return buf.getvalue()


def _png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _png_header_only(width, height):
    # IHDR declarando dimensões grandes; sem IDAT real (o limite de pixels vem antes).
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IEND", b"")


def _padded_png(size):
    """PNG válido com chunk ancilar privado preenchendo até `size` bytes exatos."""
    base = _image_bytes("PNG")
    iend = base[-12:]
    overhead = len(base) + 12  # 12 = length + type + crc do chunk de padding
    pad = size - overhead
    assert pad >= 0
    return base[:-12] + _png_chunk(b"prVt", b"\0" * pad) + iend


SAMPLES = {
    "pdf": _pdf_bytes(),
    "doc": PLAIN_DOC_FIXTURE.read_bytes(),
    "docx": _docx_bytes(),
    "txt": "Relato do reclamante: jornada das 8h às 20h.\n".encode("utf-8"),
    "jpg": _image_bytes("JPEG"),
    "png": _image_bytes("PNG"),
    "webp": _image_bytes("WEBP"),
}

# extensão → (content_type declarado típico, mime canônico persistido)
FORMATS = {
    "pdf": ("application/pdf", "application/pdf"),
    "doc": ("application/msword", "application/msword"),
    "docx": (_DOCX_MIME, _DOCX_MIME),
    "txt": ("text/plain", "text/plain"),
    "jpg": ("image/jpeg", "image/jpeg"),
    "jpeg": ("image/jpeg", "image/jpeg"),
    "png": ("image/png", "image/png"),
    "webp": ("image/webp", "image/webp"),
    "mp3": ("audio/mpeg", "audio/mpeg"),
    "wav": ("audio/wav", "audio/wav"),
    "m4a": ("audio/mp4", "audio/mp4"),
    "mp4": ("video/mp4", "video/mp4"),
    "mov": ("video/quicktime", "video/quicktime"),
    "webm": ("video/webm", "video/webm"),
}
MEDIA_EXTS = ["m4a", "mov", "mp3", "mp4", "wav", "webm"]
DOC_IMAGE_EXTS = sorted(set(FORMATS) - set(MEDIA_EXTS))


_FFMPEG_RECIPES = {
    "mp3": ["-f", "lavfi", "-i", "sine=frequency=440:duration=0.5", "-c:a", "libmp3lame"],
    "wav": ["-f", "lavfi", "-i", "sine=frequency=440:duration=0.5", "-c:a", "pcm_s16le"],
    "m4a": ["-f", "lavfi", "-i", "sine=frequency=440:duration=0.5", "-c:a", "aac"],
    "mp4": ["-f", "lavfi", "-i", "color=c=blue:s=32x32:d=0.5", "-c:v", "mpeg4"],
    "mov": ["-f", "lavfi", "-i", "color=c=blue:s=32x32:d=0.5", "-c:v", "mpeg4"],
    "webm": ["-f", "lavfi", "-i", "color=c=blue:s=32x32:d=0.5", "-c:v", "libvpx"],
}


@pytest.fixture(scope="module")
def media_samples(tmp_path_factory):
    if not HAS_FFMPEG:
        pytest.skip("ffmpeg/ffprobe indisponível no ambiente")
    out_dir = tmp_path_factory.mktemp("media_samples")
    samples = {}
    for ext, args in _FFMPEG_RECIPES.items():
        out = out_dir / f"sample.{ext}"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, str(out)],
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=60,
        )
        samples[ext] = out.read_bytes()
    return samples


def _sample(ext, media_samples=None):
    if ext in MEDIA_EXTS:
        return media_samples[ext]
    return SAMPLES["jpg" if ext == "jpeg" else ext]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_headers(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_upload_{uuid.uuid4().hex[:8]}@example.com",
        "password": "dev",
        "role": "admin",
    }
    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": "test-seed-token"},
    )
    assert r_seed.status_code == 200

    r_login = client.post(
        "/api/v1/auth/login",
        json={"username": seed_payload["username"], "password": seed_payload["password"]},
    )
    assert r_login.status_code == 200
    return {"Authorization": f"Bearer {r_login.json()['access_token']}"}


def _create_case(client, headers):
    r_case = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"UPL-{uuid.uuid4().hex[:8]}",
            "title": "Caso para política de upload",
            "description": "Validação da política de anexos.",
            "status": "draft",
        },
        headers=headers,
    )
    assert r_case.status_code == 200
    return r_case.json()["id"]


@pytest.fixture
def storage_dir(monkeypatch, tmp_path):
    path = tmp_path / "case_attachments"
    monkeypatch.setattr(settings, "CASE_ATTACHMENT_STORAGE_DIR", str(path))
    return path


@pytest.fixture
def ctx(client, monkeypatch, storage_dir):
    headers = _auth_headers(client, monkeypatch)
    case_id = _create_case(client, headers)
    return {"client": client, "headers": headers, "case_id": case_id, "storage": storage_dir}


def _upload(ctx, filename, content, content_type, category="outro"):
    return ctx["client"].post(
        f"/api/v1/cases/{ctx['case_id']}/attachments",
        data={"category": category},
        files={"file": (filename, content, content_type)},
        headers=ctx["headers"],
    )


def _stored_files(storage):
    if not storage.exists():
        return []
    return [p for p in storage.rglob("*") if p.is_file()]


def _attachment_count(db_session):
    db_session.expire_all()
    return db_session.query(CaseAttachment).count()


def _assert_nothing_persisted(ctx, db_session):
    assert _stored_files(ctx["storage"]) == []
    assert _attachment_count(db_session) == 0


def _assert_rejected(ctx, db_session, response, status, detail=None):
    assert response.status_code == status, response.text
    if detail is not None:
        assert response.json()["detail"] == detail
    _assert_nothing_persisted(ctx, db_session)


# ---------------------------------------------------------------------------
# Formatos permitidos
# ---------------------------------------------------------------------------

def _assert_accepted(ctx, db_session, ext, content):
    declared, expected_mime = FORMATS[ext]
    r = _upload(ctx, f"prova.{ext}", content, declared)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mime_type"] == expected_mime
    assert body["file_size_bytes"] == len(content)
    stored = _stored_files(ctx["storage"])
    assert len(stored) == 1
    assert stored[0].read_bytes() == content
    assert _attachment_count(db_session) == 1


@pytest.mark.parametrize("ext", DOC_IMAGE_EXTS)
def test_allowed_document_and_image_format_is_accepted(ctx, db_session, ext):
    _assert_accepted(ctx, db_session, ext, _sample(ext))


@requires_ffmpeg
@pytest.mark.parametrize("ext", MEDIA_EXTS)
def test_allowed_media_format_is_accepted(ctx, db_session, media_samples, ext):
    _assert_accepted(ctx, db_session, ext, _sample(ext, media_samples))


@pytest.mark.parametrize(
    "filename,ext",
    [("PROVA.PDF", "pdf"), ("Prova.Pdf", "pdf"), ("foto.JPG", "jpg"), ("foto.JpEg", "jpeg"), ("Relato.TXT", "txt")],
)
def test_extension_is_case_insensitive(ctx, filename, ext):
    r = _upload(ctx, filename, _sample(ext), FORMATS[ext][0])
    assert r.status_code == 200, r.text
    assert r.json()["mime_type"] == FORMATS[ext][1]


@requires_ffmpeg
@pytest.mark.parametrize("filename,ext", [("audio.MP3", "mp3"), ("video.MoV", "mov")])
def test_media_extension_is_case_insensitive(ctx, media_samples, filename, ext):
    r = _upload(ctx, filename, _sample(ext, media_samples), FORMATS[ext][0])
    assert r.status_code == 200, r.text
    assert r.json()["mime_type"] == FORMATS[ext][1]


@pytest.mark.parametrize("declared", ["", "application/octet-stream", "APPLICATION/PDF", "application/pdf; charset=binary"])
def test_persisted_mime_is_canonical_not_client_declared(ctx, db_session, declared):
    r = _upload(ctx, "prova.pdf", SAMPLES["pdf"], declared)
    assert r.status_code == 200, r.text
    assert r.json()["mime_type"] == "application/pdf"
    db_session.expire_all()
    assert db_session.query(CaseAttachment).one().mime_type == "application/pdf"


@pytest.mark.parametrize("declared", ["image/pjpeg", "image/jpeg"])
def test_jpeg_alias_is_persisted_as_canonical(ctx, declared):
    r = _upload(ctx, "foto.jpeg", SAMPLES["jpg"], declared)
    assert r.status_code == 200, r.text
    assert r.json()["mime_type"] == "image/jpeg"


# ---------------------------------------------------------------------------
# Formatos fora da whitelist, conteúdo divergente e content_type incompatível
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "filename,content,declared",
    [
        ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
        ("script.sh", b"#!/bin/sh\necho oi\n", "text/x-shellscript"),
        ("pagina.html", b"<html></html>", "text/html"),
        ("vetor.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml"),
        ("macro.docm", _docx_bytes(), "application/vnd.ms-word.document.macroEnabled.12"),
        ("pacote.zip", _docx_bytes(), "application/zip"),
        ("prova.pdf.exe", SAMPLES["pdf"], "application/pdf"),
        ("semextensao", SAMPLES["pdf"], "application/pdf"),
        ("planilha.xlsx", _docx_bytes(), "application/octet-stream"),
        ("imagem.gif", b"GIF89a" + b"\x00" * 16, "image/gif"),
    ],
)
def test_disallowed_format_is_rejected_415(ctx, db_session, filename, content, declared):
    r = _upload(ctx, filename, content, declared)
    _assert_rejected(ctx, db_session, r, 415, "Unsupported attachment format")


@pytest.mark.parametrize(
    "filename,content,declared",
    [
        ("prova.pdf", SAMPLES["png"], "application/pdf"),
        ("prova.pdf", b"%PDF-1.4\n% prova trabalhista fake\n%%EOF\n", "application/pdf"),
        ("foto.png", SAMPLES["jpg"], "image/png"),
        ("foto.jpg", SAMPLES["png"], "image/jpeg"),
        ("foto.webp", SAMPLES["png"], "image/webp"),
        ("foto.png", b"MZ\x90\x00" + b"\x00" * 64, "image/png"),
        ("contrato.docx", SAMPLES["pdf"], _DOCX_MIME),
        ("contrato.doc", _docx_bytes(), "application/msword"),
        ("contrato.doc", SAMPLES["pdf"], "application/msword"),
        ("contrato.docx", SAMPLES["doc"], _DOCX_MIME),
    ],
)
def test_content_mismatch_is_rejected_415(ctx, db_session, filename, content, declared):
    r = _upload(ctx, filename, content, declared)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@pytest.mark.parametrize(
    "filename,declared",
    [
        ("prova.pdf", "image/png"),
        ("prova.pdf", "text/html"),
        ("foto.png", "image/jpeg"),
        ("relato.txt", "application/pdf"),
        ("contrato.docx", "application/msword"),
    ],
)
def test_incompatible_declared_content_type_is_rejected_415(ctx, db_session, filename, declared):
    ext = filename.rsplit(".", 1)[1]
    r = _upload(ctx, filename, _sample(ext), declared)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content type does not match extension")


def test_outro_category_accepts_allowed_format(ctx):
    r = _upload(ctx, "relato.txt", SAMPLES["txt"], "text/plain", category="outro")
    assert r.status_code == 200, r.text
    assert r.json()["category"] == "outro"


@pytest.mark.parametrize(
    "filename,content,declared",
    [
        ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
        ("prova.pdf", b"MZ\x90\x00", "application/pdf"),
    ],
)
def test_outro_category_is_not_a_format_bypass(ctx, db_session, filename, content, declared):
    r = _upload(ctx, filename, content, declared, category="outro")
    _assert_rejected(ctx, db_session, r, 415)


@pytest.mark.parametrize("filename,content", [("prova.pdf", SAMPLES["pdf"]), ("malware.exe", b"MZ\x90\x00")])
def test_invalid_category_is_rejected_422(ctx, db_session, filename, content):
    r = _upload(ctx, filename, content, "application/pdf", category="categoria_inexistente")
    _assert_rejected(ctx, db_session, r, 422, "Invalid attachment category")


@pytest.mark.parametrize("ext", ["pdf", "txt", "png", "docx", "mp4"])
def test_empty_file_is_rejected_422(ctx, db_session, ext):
    r = _upload(ctx, f"vazio.{ext}", b"", FORMATS[ext][0])
    _assert_rejected(ctx, db_session, r, 422, "Empty attachment")


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def test_encrypted_pdf_is_rejected_415(ctx, db_session):
    r = _upload(ctx, "protegido.pdf", _encrypted_pdf_bytes(), "application/pdf")
    _assert_rejected(ctx, db_session, r, 415, "Encrypted PDF attachments are not allowed")


def test_truncated_pdf_is_rejected_415(ctx, db_session):
    truncated = SAMPLES["pdf"][: len(SAMPLES["pdf"]) // 2]
    r = _upload(ctx, "truncado.pdf", truncated, "application/pdf")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


# ---------------------------------------------------------------------------
# DOC
# ---------------------------------------------------------------------------

def test_real_word97_doc_fixture_is_accepted(ctx, db_session):
    assert PLAIN_DOC_FIXTURE.stat().st_size == 9728
    _assert_accepted(ctx, db_session, "doc", SAMPLES["doc"])


@pytest.mark.parametrize(
    "content",
    [
        b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 512,  # assinatura OLE2 sem estrutura válida
        b"garbage" * 100,
    ],
)
def test_invalid_doc_is_rejected_415(ctx, db_session, content):
    r = _upload(ctx, "contrato.doc", content, "application/msword")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


def test_real_doc_with_vba_fixture_is_rejected_415(ctx, db_session):
    # Fixture real (sem monkeypatch): Apache POI SimpleMacro.doc; procedência em VBA_DOC_FIXTURE.
    content = VBA_DOC_FIXTURE.read_bytes()
    assert hashlib.sha256(content).hexdigest() == VBA_DOC_SHA256
    r = _upload(ctx, "macro.doc", content, "application/msword")
    _assert_rejected(ctx, db_session, r, 415, "DOC attachments with macros/VBA are not allowed")


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

_ARCHIVE_LIMITS = "DOCX attachment exceeds archive limits"


def test_docx_with_too_many_entries_is_rejected_415(ctx, db_session):
    extra = [(f"word/media/p{i}.xml", "<x/>") for i in range(acv.DOCX_MAX_ENTRIES)]
    r = _upload(ctx, "muitos.docx", _docx_bytes(extra_entries=extra), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _ARCHIVE_LIMITS)


def test_docx_exceeding_uncompressed_total_is_rejected_415(ctx, db_session):
    # blocos semi-aleatórios: razão ~44:1 (abaixo de 100:1), total > 100 MiB descompactado.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml())
        zf.writestr("_rels/.rels", _RELS_XML)
        zf.writestr("word/document.xml", _DOCUMENT_XML)
        block_count = acv.DOCX_MAX_UNCOMPRESSED_BYTES // len(_random_block()) + 1
        zf.writestr("word/media/grande.bin", b"".join(_random_block() for _ in range(block_count)))
    content = buf.getvalue()
    assert len(content) < DOC_IMAGE_LIMIT
    r = _upload(ctx, "grande.docx", content, _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _ARCHIVE_LIMITS)


def _random_block():
    return os.urandom(1024) + b"\0" * (49 * 1024)


def test_docx_exceeding_compression_ratio_is_rejected_415(ctx, db_session):
    bomb = [("word/media/zeros.bin", b"\0" * (20 * 1024 * 1024))]
    r = _upload(ctx, "bomba.docx", _docx_bytes(extra_entries=bomb), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _ARCHIVE_LIMITS)


def test_docx_without_document_xml_is_rejected_415(ctx, db_session):
    r = _upload(ctx, "incompleto.docx", _docx_bytes(document=None), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


def test_docx_without_main_override_is_rejected_415(ctx, db_session):
    content_types = _content_types_xml(main_content_type="application/xml")
    r = _upload(ctx, "semoverride.docx", _docx_bytes(content_types=content_types), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


def test_macro_enabled_docx_is_rejected_415(ctx, db_session):
    content_types = _content_types_xml(main_content_type="application/vnd.ms-word.document.macroEnabled.main+xml")
    r = _upload(ctx, "macro.docx", _docx_bytes(content_types=content_types), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Macro-enabled DOCX attachments are not allowed")


@pytest.mark.parametrize(
    "entry_name",
    [
        "word/vbaProject.bin",
        "word/VBAPROJECT.BIN",
        "word/vbaproject.bin",
        "vbaProject.bin",
        "customXml/item1/vbaProject.bin",
        "word\\vbaProject.bin",
        "word/vbaProject.bin.",
    ],
)
def test_docx_with_vba_project_entry_is_rejected_415_without_macro_content_type(ctx, db_session, entry_name):
    # pacote estruturalmente aceitável (Content-Type principal não macroEnabled),
    # mas contendo vbaProject.bin: rejeitado mesmo assim (decisão DICO 2026-10-05).
    content = _docx_bytes(extra_entries=[(entry_name, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 504)])
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        assert entry_name in zf.namelist()
        assert b"macroenabled" not in zf.read("[Content_Types].xml").lower()
    r = _upload(ctx, "vba.docx", content, _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Macro-enabled DOCX attachments are not allowed")


def test_docx_with_xml_entity_expansion_is_rejected_415(ctx, db_session):
    entity_bomb = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;">]>'
        f'<w:document xmlns:w="{_W_NS}"><w:body><w:p><w:r><w:t>&lol2;</w:t></w:r></w:p></w:body></w:document>'
    )
    r = _upload(ctx, "entidades.docx", _docx_bytes(document=entity_bomb), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


def test_docx_with_encrypted_entry_flag_is_rejected_415(ctx, db_session):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml())
        zf.writestr("_rels/.rels", _RELS_XML)
        zf.writestr("word/document.xml", _DOCUMENT_XML)
        zf.infolist()[-1].flag_bits |= 0x1
    r = _upload(ctx, "cifrado.docx", buf.getvalue(), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


def test_docx_with_invalid_xml_is_rejected_415(ctx, db_session):
    r = _upload(ctx, "quebrado.docx", _docx_bytes(document="<w:document"), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


# --- Ciclo 3: endurecimento estrutural do DOCX ---

_MISMATCH = "Attachment content does not match extension"
_DOCX_MACRO = "Macro-enabled DOCX attachments are not allowed"
_OFFICE_DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
_VBA_REL = "http://schemas.microsoft.com/office/2006/relationships/vbaProject"
_STRICT_W_NS = "http://purl.oclc.org/ooxml/wordprocessingml/main"
_STRICT_OFFICE_DOC_REL = "http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument"


def _rels_xml(relationships, namespace="http://schemas.openxmlformats.org/package/2006/relationships", root="Relationships"):
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<{root} xmlns="{namespace}">{relationships}</{root}>'
    )


def _office_doc_rel(target="word/document.xml", rel_type=_OFFICE_DOC_REL, extra_attrs="", rel_id="rId1"):
    return f'<Relationship Id="{rel_id}" Type="{rel_type}" Target="{target}"{extra_attrs}/>'


def _zip_with_duplicates(entries):
    buf = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # zipfile só emite UserWarning para nome duplicado
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in entries:
                zf.writestr(name, data)
    return buf.getvalue()


def test_docx_is_parsed_and_accepted_baseline(ctx, db_session):
    # controle positivo para os casos adversariais abaixo
    _assert_accepted(ctx, db_session, "docx", _docx_bytes())


def test_strict_ooxml_docx_is_accepted(ctx, db_session):
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_STRICT_W_NS}"><w:body><w:p/></w:body></w:document>'
    )
    rels = _rels_xml(_office_doc_rel(rel_type=_STRICT_OFFICE_DOC_REL))
    _assert_accepted(ctx, db_session, "docx", _docx_bytes(document=document, rels=rels))


@pytest.mark.parametrize(
    "duplicate_name",
    ["word/document.xml", "Word/Document.xml", "WORD/DOCUMENT.XML", "word\\document.xml", "/word/document.xml",
     "[content_types].xml", "_RELS/.RELS"],
)
def test_docx_with_duplicate_part_name_is_rejected_415(ctx, db_session, duplicate_name):
    evil = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_W_NS}"><w:body><w:p><w:r><w:t>outro</w:t></w:r></w:p></w:body></w:document>'
    )
    content = _zip_with_duplicates(
        [
            ("[Content_Types].xml", _content_types_xml()),
            ("_rels/.rels", _RELS_XML),
            ("word/document.xml", _DOCUMENT_XML),
            (duplicate_name, evil),
        ]
    )
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        assert len(zf.infolist()) == 4
    r = _upload(ctx, "duplicado.docx", content, _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _MISMATCH)


@pytest.mark.parametrize(
    "rels",
    [
        None,  # _rels/.rels ausente
        _rels_xml(""),  # sem relacionamento officeDocument
        _rels_xml(_office_doc_rel(target="word/outro.xml")),
        _rels_xml(_office_doc_rel(target="../word/document.xml")),
        _rels_xml(_office_doc_rel(target="https://exemplo.invalid/document.xml", extra_attrs=' TargetMode="External"')),
        _rels_xml(_office_doc_rel(extra_attrs=' TargetMode="External"')),
        _rels_xml(_office_doc_rel() + _office_doc_rel(rel_id="rId2")),  # officeDocument duplicado
        _rels_xml(_office_doc_rel(rel_type=_OFFICE_DOC_REL.upper())),  # tipo não reconhecido
        _rels_xml(_office_doc_rel(), namespace="urn:outro"),
        _rels_xml(_office_doc_rel(), root="Relacoes"),
        "<Relationships/>",  # sem namespace
    ],
    ids=["missing", "no-office-document", "wrong-target", "traversal-target", "external-url", "external-mode",
         "two-office-documents", "unknown-rel-type", "wrong-namespace", "wrong-root", "no-namespace"],
)
def test_docx_with_invalid_package_relationships_is_rejected_415(ctx, db_session, rels):
    r = _upload(ctx, "rels.docx", _docx_bytes(rels=rels), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _MISMATCH)


def test_docx_with_absolute_office_document_target_is_accepted(ctx, db_session):
    rels = _rels_xml(_office_doc_rel(target="/word/document.xml"))
    _assert_accepted(ctx, db_session, "docx", _docx_bytes(rels=rels))


@pytest.mark.parametrize(
    "content_types",
    [
        _content_types_xml().replace(
            "http://schemas.openxmlformats.org/package/2006/content-types", "urn:outro"
        ),
        _content_types_xml().replace("<Types ", "<Tipos ").replace("</Types>", "</Tipos>"),
        '<?xml version="1.0"?><Types/>',
    ],
    ids=["wrong-namespace", "wrong-root", "no-namespace"],
)
def test_docx_with_invalid_content_types_root_is_rejected_415(ctx, db_session, content_types):
    r = _upload(ctx, "tipos.docx", _docx_bytes(content_types=content_types), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _MISMATCH)


@pytest.mark.parametrize(
    "document",
    [
        _DOCUMENT_XML.replace(_W_NS, "urn:outro"),
        _DOCUMENT_XML.replace("w:document", "w:documento"),
        "<document><body/></document>",
        f'<w:body xmlns:w="{_W_NS}"/>',
    ],
    ids=["wrong-namespace", "wrong-root", "no-namespace", "body-as-root"],
)
def test_docx_with_invalid_document_root_is_rejected_415(ctx, db_session, document):
    r = _upload(ctx, "raiz.docx", _docx_bytes(document=document), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _MISMATCH)


def test_docx_with_invalid_part_relationships_root_is_rejected_415(ctx, db_session):
    extra = [("word/_rels/document.xml.rels", "<Relacoes/>")]
    r = _upload(ctx, "rels2.docx", _docx_bytes(extra_entries=extra), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _MISMATCH)


@pytest.mark.parametrize(
    "extra_types",
    [
        '<Override PartName="/word/dados.bin" ContentType="application/vnd.ms-office.vbaProject"/>',
        '<Default Extension="dat" ContentType="application/vnd.ms-office.vbaProject"/>',
        '<Override PartName="/word/dados.xml" ContentType="application/vnd.ms-word.vbaData+xml"/>',
        '<Override PartName="/word/dados.bin" ContentType="APPLICATION/VND.MS-OFFICE.VBAPROJECT"/>',
    ],
    ids=["override", "default-renamed-extension", "vba-data", "uppercase"],
)
def test_docx_with_renamed_vba_part_by_content_type_is_rejected_415(ctx, db_session, extra_types):
    # parte VBA renomeada (o nome vbaProject.bin não aparece em lugar algum)
    content = _docx_bytes(
        content_types=_content_types_xml(extra=extra_types),
        extra_entries=[("word/dados.bin", b"\xd0\xcf\x11\xe0" + b"\x00" * 60), ("word/payload.dat", b"\x00" * 64)],
    )
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        assert not any("vbaproject.bin" in name.lower() for name in zf.namelist())
    r = _upload(ctx, "vba-ct.docx", content, _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _DOCX_MACRO)


@pytest.mark.parametrize(
    "rel_type",
    [_VBA_REL, _VBA_REL.upper(), "http://schemas.microsoft.com/office/2006/relationships/wordVbaData"],
    ids=["vba-project", "uppercase", "vba-data"],
)
def test_docx_with_vba_relationship_is_rejected_415(ctx, db_session, rel_type):
    part_rels = _rels_xml(f'<Relationship Id="rId9" Type="{rel_type}" Target="dados.bin"/>')
    content = _docx_bytes(
        extra_entries=[("word/_rels/document.xml.rels", part_rels), ("word/dados.bin", b"\xd0\xcf\x11\xe0" + b"\x00" * 60)]
    )
    r = _upload(ctx, "vba-rel.docx", content, _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _DOCX_MACRO)


def test_docx_with_vba_relationship_in_package_rels_is_rejected_415(ctx, db_session):
    rels = _rels_xml(_office_doc_rel() + f'<Relationship Id="rId9" Type="{_VBA_REL}" Target="word/dados.bin"/>')
    r = _upload(ctx, "vba-rel-pkg.docx", _docx_bytes(rels=rels), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _DOCX_MACRO)


@pytest.mark.parametrize("target", ["word/document.xml", "word/media/imagem.bin"])
def test_docx_with_crc_mismatch_is_rejected_415(ctx, db_session, target):
    payload = b"CONTEUDO-ORIGINAL-" * 8
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml())
        zf.writestr("_rels/.rels", _RELS_XML)
        if target == "word/document.xml":
            zf.writestr("word/document.xml", _DOCUMENT_XML)
        else:
            zf.writestr("word/document.xml", _DOCUMENT_XML)
            zf.writestr(target, payload)
    content = bytearray(buf.getvalue())
    original = _DOCUMENT_XML.encode() if target == "word/document.xml" else payload
    marker = b"reclamante" if target == "word/document.xml" else b"ORIGINAL"
    offset = content.index(original) + original.index(marker)
    content[offset] ^= 0x20  # altera um byte sem mudar tamanhos: só o CRC-32 denuncia
    with zipfile.ZipFile(io.BytesIO(bytes(content))) as zf:
        assert zf.testzip() == target
    r = _upload(ctx, "crc.docx", bytes(content), _DOCX_MIME)
    _assert_rejected(ctx, db_session, r, 415, _MISMATCH)


# ---------------------------------------------------------------------------
# TXT
# ---------------------------------------------------------------------------

def test_utf8_txt_with_bom_is_accepted(ctx, db_session):
    content = b"\xef\xbb\xbf" + "Relato com acentuação.\r\n\tLinha 2\n".encode("utf-8")
    _assert_accepted(ctx, db_session, "txt", content)


@pytest.mark.parametrize(
    "content",
    [
        "Relato com acentuação.".encode("latin-1"),
        "Relato".encode("utf-16"),
        "Relato".encode("utf-16-le"),
        b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 32,
        b"texto\x00oculto",
        b"acentua\xc3\xa7\xc3",  # sequência UTF-8 multibyte truncada no fim
    ],
)
def test_non_utf8_txt_is_rejected_415(ctx, db_session, content):
    r = _upload(ctx, "relato.txt", content, "text/plain")
    _assert_rejected(ctx, db_session, r, 415, "TXT attachments must be UTF-8 text")


# ---------------------------------------------------------------------------
# Imagens
# ---------------------------------------------------------------------------

def test_image_over_pixel_limit_is_rejected_415(ctx, db_session):
    content = _png_header_only(10000, 6000)  # 60 MP > 50 MP
    r = _upload(ctx, "gigante.png", content, "image/png")
    _assert_rejected(ctx, db_session, r, 415, "Image attachment exceeds pixel limit")


@pytest.mark.parametrize("ext", ["jpg", "png", "webp"])
def test_truncated_image_is_rejected_415(ctx, db_session, ext):
    data = _sample(ext)
    r = _upload(ctx, f"truncada.{ext}", data[: len(data) // 2], FORMATS[ext][0])
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


# ---------------------------------------------------------------------------
# Mídia (ffprobe + passagem completa ffmpeg, sob wrapper de limites)
# ---------------------------------------------------------------------------

_FAKE_BIN_DIR = "/opt/fake"
_FAKE_FFPROBE = f"{_FAKE_BIN_DIR}/ffprobe"
_FAKE_FFMPEG = f"{_FAKE_BIN_DIR}/ffmpeg"
_EXPECTED_LIMIT_SCRIPT = 'ulimit -t 10 || exit 126; ulimit -v 524288 || exit 126; exec "$0" "$@"'


def _fake_which(name):
    return f"{_FAKE_BIN_DIR}/{name}" if name in ("ffprobe", "ffmpeg") else None


def _fake_ffprobe_result(format_name, codec_types, returncode=0, codec_names=None, attached_pic=None, major_brand=None):
    streams = []
    for index, codec_type in enumerate(codec_types):
        stream = {"codec_type": codec_type}
        if codec_names is not None:
            stream["codec_name"] = codec_names[index]
        if attached_pic is not None:
            stream["disposition"] = {"attached_pic": attached_pic[index]}
        streams.append(stream)
    fmt = {"format_name": format_name}
    if major_brand is not None:
        fmt["tags"] = {"major_brand": major_brand}
    payload = {"format": fmt, "streams": streams}
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=json.dumps(payload).encode(), stderr=b"")


_FFMPEG_OK = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")


def _is_probe_call(cmd):
    return "-show_entries" in cmd


def _install_fake_media_tools(monkeypatch, probe_result, ffmpeg_result=_FFMPEG_OK, calls=None):
    monkeypatch.setattr(acv.shutil, "which", _fake_which)

    def _fake_run(cmd, **kwargs):
        if calls is not None:
            calls.append((cmd, kwargs))
        return probe_result if _is_probe_call(cmd) else ffmpeg_result

    monkeypatch.setattr(acv.subprocess, "run", _fake_run)


def _media_bytes():
    return b"\x00\x00\x00\x20ftypisom" + b"\x00" * 64


_DECLARED_MIME = {"mp4": "video/mp4", "mov": "video/quicktime", "m4a": "audio/mp4"}


@pytest.mark.parametrize("missing", ["ffprobe", "ffmpeg", "both"])
def test_media_tool_absent_returns_503(ctx, db_session, monkeypatch, missing):
    monkeypatch.setattr(
        acv.shutil, "which", lambda name: None if missing in (name, "both") else _fake_which(name)
    )
    monkeypatch.setattr(acv.subprocess, "run", lambda *a, **k: pytest.fail("não deve executar sem ffprobe/ffmpeg"))
    r = _upload(ctx, "video.mp4", _media_bytes(), "video/mp4")
    _assert_rejected(ctx, db_session, r, 503, "Media validator unavailable")


def test_ffprobe_vanishing_before_exec_returns_503(ctx, db_session, monkeypatch):
    monkeypatch.setattr(acv.shutil, "which", _fake_which)

    def _missing(*args, **kwargs):
        raise FileNotFoundError(_FAKE_FFPROBE)

    monkeypatch.setattr(acv.subprocess, "run", _missing)
    r = _upload(ctx, "video.mp4", _media_bytes(), "video/mp4")
    _assert_rejected(ctx, db_session, r, 503, "Media validator unavailable")


@pytest.mark.parametrize("returncode", [126, 127])
@pytest.mark.parametrize("stage", ["probe", "full-pass"])
def test_wrapper_unavailable_exit_code_returns_503(ctx, db_session, monkeypatch, returncode, stage):
    unavailable = subprocess.CompletedProcess(args=[], returncode=returncode, stdout=b"", stderr=b"sh: falhou\n")
    good_probe = _fake_ffprobe_result(acv._MP4_FAMILY, ["video"])
    if stage == "probe":
        _install_fake_media_tools(monkeypatch, unavailable)
    else:
        _install_fake_media_tools(monkeypatch, good_probe, ffmpeg_result=unavailable)
    r = _upload(ctx, "video.mp4", _media_bytes(), "video/mp4")
    _assert_rejected(ctx, db_session, r, 503, "Media validator unavailable")


@pytest.mark.parametrize("stage", ["probe", "full-pass"])
def test_media_timeout_is_rejected_415(ctx, db_session, monkeypatch, stage):
    monkeypatch.setattr(acv.shutil, "which", _fake_which)
    good_probe = _fake_ffprobe_result(acv._MP4_FAMILY, ["video"])

    def _run(cmd, **kwargs):
        if stage == "full-pass" and _is_probe_call(cmd):
            return good_probe
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"))

    monkeypatch.setattr(acv.subprocess, "run", _run)
    r = _upload(ctx, "video.mp4", _media_bytes(), "video/mp4")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@pytest.mark.parametrize(
    "result",
    [
        _fake_ffprobe_result("mov,mp4,m4a,3gp,3g2,mj2", ["video"], returncode=1),
        _fake_ffprobe_result("mov,mp4,m4a,3gp,3g2,mj2", ["video"], returncode=-9),  # morto por sinal (ex.: RLIMIT_CPU)
        _fake_ffprobe_result("mov,mp4,m4a,3gp,3g2,mj2", ["data"]),
        _fake_ffprobe_result("mov,mp4,m4a,3gp,3g2,mj2", []),
        _fake_ffprobe_result("matroska,webm", ["video"]),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=b"nao-json", stderr=b""),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=b"{}", stderr=b""),
        subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=_fake_ffprobe_result("mov,mp4,m4a,3gp,3g2,mj2", ["video"]).stdout,
            stderr=b"[mov,mp4] moov atom not found\n",
        ),
    ],
    ids=["exit-1", "signal", "data-only", "no-streams", "wrong-demuxer", "invalid-json", "no-format", "stderr"],
)
def test_ffprobe_failure_is_rejected_415(ctx, db_session, monkeypatch, result):
    calls = []
    _install_fake_media_tools(monkeypatch, result, calls=calls)
    r = _upload(ctx, "video.mp4", _media_bytes(), "video/mp4")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")
    assert all(_is_probe_call(cmd) for cmd, _ in calls)  # a passagem completa nem chega a rodar


@pytest.mark.parametrize(
    "ffmpeg_result",
    [
        subprocess.CompletedProcess(args=[], returncode=1, stdout=b"", stderr=b""),
        subprocess.CompletedProcess(args=[], returncode=-24, stdout=b"", stderr=b""),  # SIGXCPU
        subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"[mov,mp4] stream 0, offset 0x30: partial file\n"),
    ],
    ids=["exit-1", "sigxcpu", "stderr-only"],
)
def test_ffmpeg_full_pass_failure_is_rejected_415(ctx, db_session, monkeypatch, ffmpeg_result):
    calls = []
    _install_fake_media_tools(
        monkeypatch, _fake_ffprobe_result(acv._MP4_FAMILY, ["video"]), ffmpeg_result=ffmpeg_result, calls=calls
    )
    r = _upload(ctx, "video.mp4", _media_bytes(), "video/mp4")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")
    assert [_is_probe_call(cmd) for cmd, _ in calls] == [True, False]


def test_media_validation_is_invoked_hardened(ctx, db_session, monkeypatch):
    calls = []
    _install_fake_media_tools(monkeypatch, _fake_ffprobe_result("matroska,webm", ["audio"]), calls=calls)
    r = _upload(ctx, "audio.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 64, "audio/webm")
    assert r.status_code == 200, r.text
    assert r.json()["mime_type"] == "video/webm"

    assert len(calls) == 2
    (probe_cmd, _), (full_cmd, _) = calls
    for cmd, binary in ((probe_cmd, _FAKE_FFPROBE), (full_cmd, _FAKE_FFMPEG)):
        # wrapper /bin/sh fixo: limites antes do exec; binário e argumentos só como argv
        assert cmd[:4] == ["/bin/sh", "-c", _EXPECTED_LIMIT_SCRIPT, binary]
        assert cmd[cmd.index("-protocol_whitelist") + 1] == "file"
        assert cmd[cmd.index("-format_whitelist") + 1] == "matroska,webm"
        assert cmd[cmd.index("-v") + 1] == "error"
    assert probe_cmd[-1].startswith("file:")
    assert full_cmd[full_cmd.index("-i") + 1] == probe_cmd[-1]
    assert full_cmd[4] == "-nostdin"
    assert "-xerror" in full_cmd
    assert full_cmd[full_cmd.index("-map") + 1] == "0"
    assert full_cmd[full_cmd.index("-c", 4) + 1] == "copy"
    assert full_cmd[-3:] == ["-f", "null", "-"]
    # whitelists precedem a entrada
    assert full_cmd.index("-format_whitelist") < full_cmd.index("-i")

    for _, kwargs in calls:
        assert kwargs == {
            "stdin": subprocess.DEVNULL,
            "capture_output": True,
            "timeout": 10,
            "check": False,
            "close_fds": True,
        }
    assert acv.FFPROBE_TIMEOUT_SECONDS == 10


def test_media_resource_limits_script_is_exact():
    assert acv.FFPROBE_CPU_LIMIT_SECONDS == 10
    assert acv.FFPROBE_MEMORY_LIMIT_BYTES == 512 * 1024 * 1024
    cmd = acv._limited_command("/usr/bin/ffprobe", ["-v", "error", "file:/tmp/x; rm -rf /"])
    assert cmd == ["/bin/sh", "-c", _EXPECTED_LIMIT_SCRIPT, "/usr/bin/ffprobe", "-v", "error", "file:/tmp/x; rm -rf /"]
    assert not hasattr(acv, "resource")
    assert not hasattr(acv, "_limit_ffprobe_resources")


@pytest.mark.parametrize(
    "probe,accepted",
    [
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["audio"], codec_names=["aac"]), True),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["audio", "video"], codec_names=["aac", "png"], attached_pic=[0, 1]), True),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["audio", "video"], codec_names=["aac", "h264"], attached_pic=[0, 0]), False),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["audio", "video"], codec_names=["aac", "h264"]), False),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["video"], codec_names=["png"], attached_pic=[1]), False),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["video"], codec_names=["h264"]), False),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["data"], codec_names=["bin_data"]), False),
    ],
    ids=["audio-only", "audio+cover", "audio+video", "audio+video-no-disposition", "cover-only", "video-only", "data-only"],
)
def test_m4a_stream_rules(ctx, db_session, monkeypatch, probe, accepted):
    _install_fake_media_tools(monkeypatch, probe)
    r = _upload(ctx, "audio.m4a", _media_bytes(), "audio/mp4")
    if accepted:
        assert r.status_code == 200, r.text
    else:
        _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@pytest.mark.parametrize("ext", ["mp4", "mov"])
@pytest.mark.parametrize(
    "probe,accepted",
    [
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["video"], codec_names=["h264"]), True),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["audio"], codec_names=["aac"]), True),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["video"], codec_names=["png"], attached_pic=[1]), False),
        (_fake_ffprobe_result(acv._MP4_FAMILY, ["data", "subtitle"], codec_names=["bin_data", "mov_text"]), False),
    ],
    ids=["video", "audio", "cover-only", "no-av"],
)
def test_mp4_mov_require_audio_or_video(ctx, db_session, monkeypatch, ext, probe, accepted):
    _install_fake_media_tools(monkeypatch, probe)
    r = _upload(ctx, f"midia.{ext}", _media_bytes(), _DECLARED_MIME[ext])
    if accepted:
        assert r.status_code == 200, r.text
    else:
        _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@pytest.mark.parametrize("ext", ["mp4", "mov", "m4a"])
@pytest.mark.parametrize(
    "brand,codec_types,codec_names",
    [
        ("3gp4", ["audio"], ["amr_nb"]),
        ("3gp5", ["audio"], ["amr_wb"]),
        ("3gp6", ["video", "audio"], ["h263", "aac"]),
        ("3g2a", ["audio"], ["qcelp"]),
        ("3G2B", ["audio"], ["evrc"]),
        (" 3gp4 ", ["audio"], ["amr_nb"]),
        # Opção B: marca 3G basta, independentemente do codec
        ("3gp4", ["video", "audio"], ["mpeg4", "aac"]),
        ("3gp6", ["video", "audio"], ["h264", "aac"]),
        ("3gp5", ["audio"], ["aac"]),
        ("3g2a", ["video", "audio"], ["h264", "aac"]),
        ("3GP4", ["video"], ["mpeg4"]),
    ],
)
def test_3gp_disguised_as_mp4_family_is_rejected_415(ctx, db_session, monkeypatch, ext, brand, codec_types, codec_names):
    probe = _fake_ffprobe_result(acv._MP4_FAMILY, codec_types, codec_names=codec_names, major_brand=brand)
    _install_fake_media_tools(monkeypatch, probe)
    r = _upload(ctx, f"midia.{ext}", _media_bytes(), _DECLARED_MIME[ext])
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@pytest.mark.parametrize(
    "brand,codec_types,codec_names",
    [
        ("isom", ["audio"], ["amr_nb"]),  # codec 3GPP sem marca 3G: critério é só a marca
        ("mp42", ["video"], ["h263"]),
        (None, ["audio"], ["amr_nb"]),
        ("isom", ["video", "audio"], ["h264", "aac"]),
        ("mp41", ["video", "audio"], ["mpeg4", "aac"]),
        ("qt  ", ["video", "audio"], ["h264", "aac"]),
        ("M4A ", ["audio"], ["aac"]),
        ("x3gp", ["audio"], ["aac"]),  # "3g" fora do início não conta
    ],
    ids=["isom-amr", "mp42-h263", "no-brand-amr", "isom-h264", "mp41-mpeg4", "qt-h264", "m4a-aac", "x3gp-aac"],
)
def test_3gp_criterion_depends_only_on_brand(ctx, db_session, monkeypatch, brand, codec_types, codec_names):
    probe = _fake_ffprobe_result(acv._MP4_FAMILY, codec_types, codec_names=codec_names, major_brand=brand)
    _install_fake_media_tools(monkeypatch, probe)
    r = _upload(ctx, "midia.mp4", _media_bytes(), "video/mp4")
    assert r.status_code == 200, r.text


# --- mídia real (ffmpeg/ffprobe do ambiente)


def _ffmpeg_encoders():
    if not HAS_FFMPEG:
        return ""
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, stdin=subprocess.DEVNULL, timeout=30, check=False
    ).stdout.decode(errors="replace")


def _make_media(tmp_path, name, *args):
    out = tmp_path / name
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, str(out)],
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=60,
    )
    return out


@requires_ffmpeg
def test_real_m4a_with_cover_art_is_accepted(ctx, db_session, tmp_path):
    cover = _make_media(tmp_path, "cover.png", "-f", "lavfi", "-i", "color=c=red:s=16x16", "-frames:v", "1")
    art = _make_media(
        tmp_path, "art.m4a",
        "-f", "lavfi", "-i", "sine=duration=0.5", "-i", str(cover),
        "-map", "0:a", "-map", "1:v", "-c:a", "aac", "-c:v", "png", "-disposition:v:0", "attached_pic",
    )
    r = _upload(ctx, "capa.m4a", art.read_bytes(), "audio/mp4")
    assert r.status_code == 200, r.text


@requires_ffmpeg
def test_real_m4a_with_video_stream_is_rejected_415(ctx, db_session, tmp_path):
    vid = _make_media(
        tmp_path, "vid.m4a",
        "-f", "lavfi", "-i", "sine=duration=0.5", "-f", "lavfi", "-i", "color=c=blue:s=32x32:d=0.5",
        "-c:a", "aac", "-c:v", "mpeg4", "-f", "ipod",
    )
    r = _upload(ctx, "video-disfarcado.m4a", vid.read_bytes(), "audio/mp4")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@requires_ffmpeg
@pytest.mark.parametrize("declared_ext", ["mp4", "mov", "m4a"])
@pytest.mark.parametrize("kind", ["amr_nb", "h263"])
def test_real_3gp_disguised_as_mp4_family_is_rejected_415(ctx, db_session, tmp_path, declared_ext, kind):
    encoders = _ffmpeg_encoders()
    if kind == "amr_nb":
        if "libopencore_amrnb" not in encoders:
            pytest.skip("encoder AMR-NB indisponível no ffmpeg do ambiente")
        src = _make_media(
            tmp_path, "amr.3gp",
            "-f", "lavfi", "-i", "sine=duration=0.5", "-ar", "8000", "-ac", "1",
            "-c:a", "libopencore_amrnb", "-b:a", "12.2k",
        )
    else:
        if " h263 " not in encoders:
            pytest.skip("encoder H.263 indisponível no ffmpeg do ambiente")
        src = _make_media(tmp_path, "h263.3gp", "-f", "lavfi", "-i", "color=c=blue:s=176x144:d=0.5", "-c:v", "h263")
    assert src.read_bytes()[8:11] == b"3gp"  # major_brand real 3GP
    r = _upload(ctx, f"midia.{declared_ext}", src.read_bytes(), _DECLARED_MIME[declared_ext])
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@requires_ffmpeg
@pytest.mark.parametrize("declared_ext", ["mp4", "mov", "m4a"])
@pytest.mark.parametrize("kind", ["mpeg4_aac", "aac"])
def test_real_3gp_with_common_codecs_is_rejected_415(ctx, db_session, tmp_path, declared_ext, kind):
    if kind == "mpeg4_aac":
        src = _make_media(
            tmp_path, "comum.3gp",
            "-f", "lavfi", "-i", "sine=duration=0.5", "-f", "lavfi", "-i", "color=c=blue:s=176x144:d=0.5",
            "-c:a", "aac", "-c:v", "mpeg4", "-f", "3gp",
        )
    else:
        src = _make_media(tmp_path, "aac.3gp", "-f", "lavfi", "-i", "sine=duration=0.5", "-c:a", "aac", "-f", "3gp")
    assert src.read_bytes()[8:11] == b"3gp"  # major_brand real 3GP com codecs comuns
    r = _upload(ctx, f"midia.{declared_ext}", src.read_bytes(), _DECLARED_MIME[declared_ext])
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@requires_ffmpeg
@pytest.mark.parametrize("ext,declared", [("mp4", "video/mp4"), ("webm", "video/webm"), ("wav", "audio/wav")])
def test_real_truncated_media_is_rejected_by_full_pass_415(ctx, db_session, media_samples, monkeypatch, ext, declared):
    data = media_samples[ext]
    truncated = data[: int(len(data) * 0.6)]
    calls = []
    real_run = acv.subprocess.run

    def _spy(cmd, **kwargs):
        result = real_run(cmd, **kwargs)
        calls.append((cmd, result))
        return result

    monkeypatch.setattr(acv.subprocess, "run", _spy)
    r = _upload(ctx, f"truncado.{ext}", truncated, declared)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")
    assert calls  # o validador real foi executado


@requires_ffmpeg
@pytest.mark.parametrize("ext", ["mp4", "webm", "wav", "mp3", "mov", "m4a"])
def test_real_media_passes_both_stages(ctx, db_session, media_samples, monkeypatch, ext):
    calls = []
    real_run = acv.subprocess.run

    def _spy(cmd, **kwargs):
        result = real_run(cmd, **kwargs)
        calls.append((cmd, result))
        return result

    monkeypatch.setattr(acv.subprocess, "run", _spy)
    r = _upload(ctx, f"ok.{ext}", media_samples[ext], "application/octet-stream")
    assert r.status_code == 200, r.text
    assert [cmd[3].rsplit("/", 1)[-1] for cmd, _ in calls] == ["ffprobe", "ffmpeg"]
    assert all(result.returncode == 0 and not result.stderr.strip() for _, result in calls)


@requires_ffmpeg
def test_real_wrapper_missing_binary_returns_503(ctx, db_session, media_samples, monkeypatch):
    monkeypatch.setattr(acv.shutil, "which", lambda name: f"/nonexistent-dir/{name}")
    r = _upload(ctx, "video.mp4", media_samples["mp4"], "video/mp4")
    _assert_rejected(ctx, db_session, r, 503, "Media validator unavailable")


@requires_ffmpeg
def test_real_wrapper_fails_closed_when_limit_cannot_be_applied(ctx, db_session, media_samples, monkeypatch):
    # valor inválido para ulimit → o shell não chega ao exec → 126 → 503 (nunca aceito sem limite)
    monkeypatch.setattr(acv, "FFPROBE_CPU_LIMIT_SECONDS", -1)
    r = _upload(ctx, "video.mp4", media_samples["mp4"], "video/mp4")
    _assert_rejected(ctx, db_session, r, 503, "Media validator unavailable")


def test_real_wrapper_enforces_memory_limit():
    import sys

    small = acv.subprocess.run(
        acv._limited_command(sys.executable, ["-I", "-c", "b = bytearray(16 * 1024 * 1024)"]),
        capture_output=True, stdin=subprocess.DEVNULL, timeout=30, check=False,
    )
    assert small.returncode == 0, small.stderr
    big = acv.subprocess.run(
        acv._limited_command(sys.executable, ["-I", "-c", "b = bytearray(600 * 1024 * 1024)"]),
        capture_output=True, stdin=subprocess.DEVNULL, timeout=30, check=False,
    )
    assert big.returncode != 0
    assert b"MemoryError" in big.stderr
    with pytest.raises(acv.UnsupportedAttachmentContent):
        acv._run_limited(sys.executable, ["-I", "-c", "b = bytearray(600 * 1024 * 1024)"])


def test_real_wrapper_reports_limits_to_child():
    import sys

    probe = acv.subprocess.run(
        acv._limited_command(
            sys.executable,
            ["-I", "-c", "import resource as r; print(r.getrlimit(r.RLIMIT_CPU)[0], r.getrlimit(r.RLIMIT_AS)[0])"],
        ),
        capture_output=True, stdin=subprocess.DEVNULL, timeout=30, check=True,
    )
    assert probe.stdout.split() == [b"10", str(512 * 1024 * 1024).encode()]


@requires_ffmpeg
@pytest.mark.parametrize(
    "filename,source_ext,declared",
    [
        ("audio.mp3", "wav", "audio/mpeg"),
        ("video.webm", "mp4", "video/webm"),
        ("audio.wav", "mp3", "audio/wav"),
        ("video.mp4", "webm", "video/mp4"),
    ],
)
def test_real_media_container_mismatch_is_rejected_415(ctx, db_session, media_samples, filename, source_ext, declared):
    r = _upload(ctx, filename, media_samples[source_ext], declared)
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


@requires_ffmpeg
def test_non_media_bytes_with_media_extension_are_rejected_415(ctx, db_session):
    r = _upload(ctx, "video.mp4", SAMPLES["pdf"], "video/mp4")
    _assert_rejected(ctx, db_session, r, 415, "Attachment content does not match extension")


# ---------------------------------------------------------------------------
# Limites exatos (leitura em chunks)
# ---------------------------------------------------------------------------

def test_policy_limits_have_exact_values():
    assert case_attachments.MAX_DOCUMENT_IMAGE_UPLOAD_BYTES == DOC_IMAGE_LIMIT
    assert case_attachments.MAX_MEDIA_UPLOAD_BYTES == MEDIA_LIMIT
    assert acv.DOCX_MAX_ENTRIES == 1000
    assert acv.DOCX_MAX_UNCOMPRESSED_BYTES == 100 * 1024 * 1024
    assert acv.DOCX_MAX_COMPRESSION_RATIO == 100
    assert acv.IMAGE_MAX_PIXELS == 50_000_000


def test_txt_at_exact_limit_is_accepted(ctx, db_session):
    content = b"a" * DOC_IMAGE_LIMIT
    r = _upload(ctx, "limite.txt", content, "text/plain")
    assert r.status_code == 200, r.text
    assert r.json()["file_size_bytes"] == DOC_IMAGE_LIMIT


def test_txt_one_byte_over_limit_is_rejected_413(ctx, db_session):
    r = _upload(ctx, "excesso.txt", b"a" * (DOC_IMAGE_LIMIT + 1), "text/plain")
    _assert_rejected(ctx, db_session, r, 413, "Attachment exceeds size limit")


def test_image_at_exact_limit_is_accepted(ctx, db_session):
    content = _padded_png(DOC_IMAGE_LIMIT)
    assert len(content) == DOC_IMAGE_LIMIT
    r = _upload(ctx, "limite.png", content, "image/png")
    assert r.status_code == 200, r.text
    assert r.json()["file_size_bytes"] == DOC_IMAGE_LIMIT


def test_image_one_byte_over_limit_is_rejected_413(ctx, db_session):
    r = _upload(ctx, "excesso.png", _padded_png(DOC_IMAGE_LIMIT + 1), "image/png")
    _assert_rejected(ctx, db_session, r, 413, "Attachment exceeds size limit")


def test_document_between_class_limits_is_rejected_413(ctx, db_session):
    # 50 MiB: acima do limite de documentos, abaixo do limite de mídia.
    r = _upload(ctx, "medio.pdf", SAMPLES["pdf"] + b"\0" * (50 * 1024 * 1024), "application/pdf")
    _assert_rejected(ctx, db_session, r, 413, "Attachment exceeds size limit")


def _padded_mp4(media_samples, size):
    base = media_samples["mp4"]
    pad = size - len(base) - 8  # cabeçalho do box `free`
    assert pad >= 0
    return base + struct.pack(">I", pad + 8) + b"free" + b"\0" * pad


@requires_ffmpeg
def test_media_at_exact_limit_is_accepted(ctx, db_session, media_samples):
    content = _padded_mp4(media_samples, MEDIA_LIMIT)
    assert len(content) == MEDIA_LIMIT
    r = _upload(ctx, "limite.mp4", content, "video/mp4")
    assert r.status_code == 200, r.text
    assert r.json()["file_size_bytes"] == MEDIA_LIMIT


def test_media_one_byte_over_limit_is_rejected_413(ctx, db_session, monkeypatch):
    # o 413 é decidido na leitura, antes de qualquer validador: não depende de ffmpeg.
    monkeypatch.setattr(acv.shutil, "which", lambda name: pytest.fail("validador não deveria rodar"))
    r = _upload(ctx, "excesso.mp4", _media_bytes() + b"\0" * (MEDIA_LIMIT + 1 - len(_media_bytes())), "video/mp4")
    _assert_rejected(ctx, db_session, r, 413, "Attachment exceeds size limit")


# ---------------------------------------------------------------------------
# Falha de persistência não deixa órfãos
# ---------------------------------------------------------------------------

def test_commit_failure_leaves_no_orphan_file_or_record(ctx, db_session, monkeypatch):
    def _failing_commit():
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(db_session, "commit", _failing_commit)

    with pytest.raises(RuntimeError, match="simulated commit failure"):
        _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")

    monkeypatch.undo()
    assert _stored_files(ctx["storage"]) == []
    assert _attachment_count(db_session) == 0


def test_ambiguous_commit_that_persisted_keeps_file_and_record(ctx, db_session, monkeypatch):
    # commit efetivado no banco, mas a chamada falha depois (ex.: conexão cai na resposta do COMMIT)
    original_commit = db_session.commit
    reconciled = []
    original_absent = case_attachments._attachment_record_absent

    def _commit_then_fail():
        original_commit()
        raise RuntimeError("simulated ambiguous commit")

    def _spy_absent(db, tenant_id, target_path):
        result = original_absent(db, tenant_id, target_path)
        reconciled.append((tenant_id, str(target_path), result))
        return result

    monkeypatch.setattr(db_session, "commit", _commit_then_fail)
    monkeypatch.setattr(case_attachments, "_attachment_record_absent", _spy_absent)

    with pytest.raises(RuntimeError, match="simulated ambiguous commit"):
        _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")

    monkeypatch.undo()
    stored = _stored_files(ctx["storage"])
    assert len(stored) == 1
    assert _attachment_count(db_session) == 1
    record = db_session.query(CaseAttachment).one()
    assert Path(record.storage_path).read_bytes() == SAMPLES["pdf"]
    assert reconciled == [(record.tenant_id, record.storage_path, False)]


def test_ambiguous_commit_not_persisted_is_reconciled_in_new_session(ctx, db_session, monkeypatch):
    sessions = []
    original_session = case_attachments.Session

    def _tracking_session(*args, **kwargs):
        session = original_session(*args, **kwargs)
        sessions.append(session)
        return session

    def _failing_commit():
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(case_attachments, "Session", _tracking_session)
    monkeypatch.setattr(db_session, "commit", _failing_commit)

    with pytest.raises(RuntimeError, match="simulated commit failure"):
        _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")

    monkeypatch.undo()
    assert len(sessions) == 1 and sessions[0] is not db_session
    assert _stored_files(ctx["storage"]) == []
    assert _attachment_count(db_session) == 0


@pytest.mark.parametrize("failure_point", ["session", "tenant", "query"])
def test_undeterminable_commit_state_preserves_file(ctx, db_session, monkeypatch, failure_point):
    def _failing_commit():
        raise RuntimeError("simulated commit failure")

    def _boom(*args, **kwargs):
        raise RuntimeError("reconciliation unavailable")

    if failure_point == "session":
        monkeypatch.setattr(case_attachments, "Session", _boom)
    elif failure_point == "tenant":
        monkeypatch.setattr(case_attachments, "set_tenant_on_session", _boom)
    else:
        original_session = case_attachments.Session

        def _session_with_failing_query(*args, **kwargs):
            session = original_session(*args, **kwargs)
            session.query = _boom
            return session

        monkeypatch.setattr(case_attachments, "Session", _session_with_failing_query)
    monkeypatch.setattr(db_session, "commit", _failing_commit)

    # o erro original é propagado, não o da reconciliação
    with pytest.raises(RuntimeError, match="simulated commit failure"):
        _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")

    monkeypatch.undo()
    stored = _stored_files(ctx["storage"])
    assert len(stored) == 1  # estado indeterminável: preserva o arquivo (sem limpeza de órfãos)
    assert stored[0].read_bytes() == SAMPLES["pdf"]
    assert _attachment_count(db_session) == 0


def test_flush_failure_leaves_no_orphan_file_or_record(ctx, db_session, monkeypatch):
    original_flush = db_session.flush

    def _failing_flush(*args, **kwargs):
        if any(isinstance(obj, CaseAttachment) for obj in db_session.new):
            raise RuntimeError("simulated flush failure")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db_session, "flush", _failing_flush)

    with pytest.raises(RuntimeError, match="simulated flush failure"):
        _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")

    assert _stored_files(ctx["storage"]) == []
    assert _attachment_count(db_session) == 0


def test_refresh_failure_leaves_no_orphan_file_or_record(ctx, db_session, monkeypatch):
    original_refresh = db_session.refresh

    def _failing_refresh(instance, *args, **kwargs):
        if isinstance(instance, CaseAttachment):
            raise RuntimeError("simulated refresh failure")
        return original_refresh(instance, *args, **kwargs)

    monkeypatch.setattr(db_session, "refresh", _failing_refresh)

    with pytest.raises(RuntimeError, match="simulated refresh failure"):
        _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")

    assert _stored_files(ctx["storage"]) == []
    assert _attachment_count(db_session) == 0


def test_successful_upload_is_flushed_and_refreshed_before_commit(ctx, db_session, monkeypatch):
    events = []
    original_flush, original_refresh, original_commit = db_session.flush, db_session.refresh, db_session.commit

    def _flush(*args, **kwargs):
        if any(isinstance(obj, CaseAttachment) for obj in db_session.new):
            events.append("flush")
        return original_flush(*args, **kwargs)

    def _refresh(instance, *args, **kwargs):
        if isinstance(instance, CaseAttachment):
            events.append("refresh")
        return original_refresh(instance, *args, **kwargs)

    def _commit():
        if "refresh" in events and "commit" not in events:
            events.append("commit")
        return original_commit()

    monkeypatch.setattr(db_session, "flush", _flush)
    monkeypatch.setattr(db_session, "refresh", _refresh)
    monkeypatch.setattr(db_session, "commit", _commit)

    r = _upload(ctx, "prova.pdf", SAMPLES["pdf"], "application/pdf")
    assert r.status_code == 200, r.text
    assert events == ["flush", "refresh", "commit"]
    body = r.json()
    assert body["id"] > 0
    assert body["created_at"]
    assert len(_stored_files(ctx["storage"])) == 1


# ---------------------------------------------------------------------------
# UploadFile fechado em todos os caminhos
# ---------------------------------------------------------------------------

class _SpyFile(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.close_calls = 0

    def close(self):
        self.close_calls += 1
        super().close()


def _direct_upload(db_session, case_id, filename, content, content_type, category="outro"):
    spy = _SpyFile(content)
    upload = UploadFile(file=spy, filename=filename, headers={"content-type": content_type})
    tenant_id = db_session.get(Case, case_id).tenant_id
    current_user = {"sub": "spy", "role": "admin", "tenant_id": tenant_id}
    try:
        result = case_attachments.upload_case_attachment(
            case_id=case_id,
            file=upload,
            category=category,
            description=None,
            event_date=None,
            db=db_session,
            current_user=current_user,
        )
        outcome = result
    except HTTPException as exc:
        outcome = exc
    return spy, outcome


def test_upload_file_closed_on_success(ctx, db_session):
    spy, outcome = _direct_upload(db_session, ctx["case_id"], "prova.pdf", SAMPLES["pdf"], "application/pdf")
    assert isinstance(outcome, CaseAttachment)
    assert spy.close_calls == 1


@pytest.mark.parametrize(
    "filename,content,content_type,category,status",
    [
        ("prova.pdf", SAMPLES["pdf"], "application/pdf", "categoria_inexistente", 422),
        ("vazio.pdf", b"", "application/pdf", "outro", 422),
        ("malware.exe", b"MZ\x90\x00", "application/octet-stream", "outro", 415),
        ("prova.pdf", SAMPLES["pdf"], "image/png", "outro", 415),
        ("falso.pdf", b"nao e pdf", "application/pdf", "outro", 415),
    ],
)
def test_upload_file_closed_on_rejection(ctx, db_session, filename, content, content_type, category, status):
    spy, outcome = _direct_upload(db_session, ctx["case_id"], filename, content, content_type, category)
    assert isinstance(outcome, HTTPException)
    assert outcome.status_code == status
    assert spy.close_calls == 1
    _assert_nothing_persisted(ctx, db_session)


def test_upload_file_closed_on_case_not_found(ctx, db_session):
    spy = _SpyFile(SAMPLES["pdf"])
    upload = UploadFile(file=spy, filename="prova.pdf", headers={"content-type": "application/pdf"})
    tenant_id = db_session.get(Case, ctx["case_id"]).tenant_id
    with pytest.raises(HTTPException) as exc_info:
        case_attachments.upload_case_attachment(
            case_id=ctx["case_id"] + 9999,
            file=upload,
            category="outro",
            description=None,
            event_date=None,
            db=db_session,
            current_user={"sub": "spy", "role": "admin", "tenant_id": tenant_id},
        )
    assert exc_info.value.status_code == 404
    assert spy.close_calls == 1


def test_upload_file_closed_on_size_limit(ctx, db_session, monkeypatch):
    monkeypatch.setitem(case_attachments._UPLOAD_FORMATS, ".txt", ("text/plain", {"text/plain"}, 4))
    spy, outcome = _direct_upload(db_session, ctx["case_id"], "relato.txt", b"12345", "text/plain")
    assert isinstance(outcome, HTTPException)
    assert outcome.status_code == 413
    assert spy.close_calls == 1
    _assert_nothing_persisted(ctx, db_session)


def test_upload_file_closed_on_validator_unavailable(ctx, db_session, monkeypatch):
    monkeypatch.setattr(acv.shutil, "which", lambda name: None)
    spy, outcome = _direct_upload(db_session, ctx["case_id"], "video.mp4", _media_bytes(), "video/mp4")
    assert isinstance(outcome, HTTPException)
    assert outcome.status_code == 503
    assert spy.close_calls == 1
    _assert_nothing_persisted(ctx, db_session)


def test_upload_file_closed_on_unexpected_error(ctx, db_session, monkeypatch):
    def _failing_commit():
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(db_session, "commit", _failing_commit)
    spy = _SpyFile(SAMPLES["pdf"])
    upload = UploadFile(file=spy, filename="prova.pdf", headers={"content-type": "application/pdf"})
    tenant_id = db_session.get(Case, ctx["case_id"]).tenant_id
    with pytest.raises(RuntimeError, match="simulated commit failure"):
        case_attachments.upload_case_attachment(
            case_id=ctx["case_id"],
            file=upload,
            category="outro",
            description=None,
            event_date=None,
            db=db_session,
            current_user={"sub": "spy", "role": "admin", "tenant_id": tenant_id},
        )
    monkeypatch.undo()
    assert spy.close_calls == 1
    _assert_nothing_persisted(ctx, db_session)


# ---------------------------------------------------------------------------
# RBAC e tenant preservados
# ---------------------------------------------------------------------------

def _create_tenant_user(db_session, role):
    tenant = Tenant(name=f"TenantUpload_{uuid.uuid4()}")
    db_session.add(tenant)
    db_session.flush()
    db_session.add(
        Subscription(
            tenant_id=tenant.id,
            plan_type="basic",
            status="active",
            case_limit=10,
            active=True,
            expires_at=datetime.now(timezone.utc),
        )
    )
    user = User(
        username=f"{role}_{uuid.uuid4()}@example.com",
        password_hash=pwd_context.hash("123456"),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(TenantMember(user_id=user.id, tenant_id=tenant.id, role=role))
    db_session.commit()
    return tenant, user


def _login(client, username):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": "123456"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.parametrize("role", ["estagiario", "leitura"])
def test_non_professional_role_cannot_upload(client, db_session, storage_dir, role):
    tenant, owner = _create_tenant_user(db_session, "admin")
    member = User(
        username=f"{role}_{uuid.uuid4()}@example.com",
        password_hash=pwd_context.hash("123456"),
        role=role,
        is_active=True,
    )
    db_session.add(member)
    db_session.flush()
    db_session.add(TenantMember(user_id=member.id, tenant_id=tenant.id, role=role))
    db_session.commit()

    case_id = _create_case(client, _login(client, owner.username))

    r = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        data={"category": "pdf"},
        files={"file": ("prova.pdf", SAMPLES["pdf"], "application/pdf")},
        headers=_login(client, member.username),
    )

    assert r.status_code == 403, r.text
    assert _stored_files(storage_dir) == []
    assert _attachment_count(db_session) == 0


def test_cross_tenant_upload_is_isolated(client, db_session, storage_dir):
    _, user_a = _create_tenant_user(db_session, "admin")
    _, user_b = _create_tenant_user(db_session, "admin")

    case_a_id = _create_case(client, _login(client, user_a.username))

    r = client.post(
        f"/api/v1/cases/{case_a_id}/attachments",
        data={"category": "pdf"},
        files={"file": ("prova.pdf", SAMPLES["pdf"], "application/pdf")},
        headers=_login(client, user_b.username),
    )

    assert r.status_code == 404, r.text
    assert _stored_files(storage_dir) == []
    assert _attachment_count(db_session) == 0


# ---------------------------------------------------------------------------
# PostgreSQL/RLS — reconciliação de anexos sob role de runtime sem BYPASSRLS
# ---------------------------------------------------------------------------
# Estes testes não simulam a corrida temporal do COMMIT e não comprovam sua
# ausência: verificam apenas visibilidade da reconciliação sob RLS real e a
# preservação do arquivo quando o commit persistiu antes de uma exceção.


def _pg_seed_case(pg_request_db):
    db = pg_request_db()
    try:
        role = db.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        ).one()
        assert tuple(role) == (False, False)

        tenant_a = Tenant(name="PG Tenant A")
        tenant_b = Tenant(name="PG Tenant B")
        db.add_all([tenant_a, tenant_b])
        db.commit()

        set_tenant_on_session(db, tenant_a.id)
        case = Case(
            case_number="PG-A-001",
            title="Caso PG A",
            description="Caso PG A",
            status="draft",
            tenant_id=tenant_a.id,
        )
        db.add(case)
        db.commit()
        return tenant_a.id, tenant_b.id, case.id
    finally:
        db.close()


def _pg_upload(db, tenant_id, case_id):
    # Espelha require_auth (app/core/security.py), que seta o tenant na sessão
    # da request antes de qualquer acesso a tabela com RLS.
    set_tenant_on_session(db, tenant_id)
    upload = UploadFile(
        file=io.BytesIO(SAMPLES["pdf"]),
        filename="prova.pdf",
        headers={"content-type": "application/pdf"},
    )
    return case_attachments.upload_case_attachment(
        case_id=case_id,
        file=upload,
        category="outro",
        description=None,
        event_date=None,
        db=db,
        current_user={"sub": "pg", "role": "admin", "tenant_id": tenant_id},
    )


def _pg_attachments(pg_request_db, tenant_id):
    db = pg_request_db()
    try:
        set_tenant_on_session(db, tenant_id)
        return [(row.tenant_id, row.storage_path) for row in db.query(CaseAttachment).all()]
    finally:
        db.close()


@pytest.mark.pg
def test_pg_reconciliation_respects_tenant_rls(pg_request_db, storage_dir):
    tenant_a, tenant_b, case_id = _pg_seed_case(pg_request_db)

    db = pg_request_db()
    try:
        record = _pg_upload(db, tenant_a, case_id)
        stored_path = Path(record.storage_path)
    finally:
        db.close()

    assert stored_path.read_bytes() == SAMPLES["pdf"]

    probe = pg_request_db()
    try:
        # Tenant A: registro persistido visível na sessão nova de reconciliação.
        assert case_attachments._attachment_record_absent(probe, tenant_a, stored_path) is False
        # Tenant B: RLS oculta o registro de A.
        assert case_attachments._attachment_record_absent(probe, tenant_b, stored_path) is True
        # Caminho inexistente sob tenant A.
        missing = stored_path.with_name(f"{uuid.uuid4().hex}.pdf")
        assert case_attachments._attachment_record_absent(probe, tenant_a, missing) is True
    finally:
        probe.close()

    assert stored_path.read_bytes() == SAMPLES["pdf"]
    assert _pg_attachments(pg_request_db, tenant_a) == [(tenant_a, str(stored_path))]
    assert _pg_attachments(pg_request_db, tenant_b) == []


@pytest.mark.pg
def test_pg_commit_persisted_then_exception_keeps_file(pg_request_db, storage_dir, monkeypatch):
    tenant_a, tenant_b, case_id = _pg_seed_case(pg_request_db)

    db = pg_request_db()
    try:
        original_commit = db.commit

        def _commit_then_fail():
            original_commit()
            raise RuntimeError("simulated ambiguous commit")

        monkeypatch.setattr(db, "commit", _commit_then_fail)
        with pytest.raises(RuntimeError, match="simulated ambiguous commit"):
            _pg_upload(db, tenant_a, case_id)
        monkeypatch.undo()
    finally:
        db.close()

    persisted = _pg_attachments(pg_request_db, tenant_a)
    assert len(persisted) == 1
    stored_path = Path(persisted[0][1])
    assert _stored_files(storage_dir) == [stored_path]
    assert stored_path.read_bytes() == SAMPLES["pdf"]
    assert _pg_attachments(pg_request_db, tenant_b) == []
