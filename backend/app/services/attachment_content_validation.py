"""Validação estrutural do conteúdo de anexos de caso (Política F4, Arquitetura A).

Cada formato da whitelist é validado pelo parser especializado aprovado:
PDF via pypdf (strict), DOC via olefile, DOCX via zipfile + defusedxml,
TXT como UTF-8, imagens via Pillow (verify + decode) e mídia via ffprobe
seguido de passagem completa do ffmpeg (``-c copy -f null``), ambos em
subprocesso com timeout e limites de CPU/memória aplicados por ``ulimit`` em
``/bin/sh``. Toda falha é fail-closed.

Limitações aceitas: a passagem completa demuxa sem decodificar, então MP3
truncado e parte das corrupções de payload em WAV/M4A/MP3 podem não ser
detectadas. A rejeição de 3GP/3GP2 em .mp4/.mov/.m4a usa apenas o major_brand
("3g*"), sem considerar codec: reescrita da marca no ftyp ou remux para MP4
contornam o critério, que não é prova de origem. Validar o formato não equivale
a antivírus.
"""

from __future__ import annotations

import codecs
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import olefile
from defusedxml import ElementTree as SafeElementTree
from PIL import Image
from pypdf import PdfReader


class UnsupportedAttachmentContent(Exception):
    """Conteúdo inválido, incompatível com a extensão ou rejeitado pela política (HTTP 415)."""


class AttachmentValidatorUnavailable(Exception):
    """Validador externo necessário indisponível no ambiente (HTTP 503)."""


_READ_CHUNK_BYTES = 1024 * 1024

DOCX_MAX_ENTRIES = 1000
DOCX_MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
DOCX_MAX_COMPRESSION_RATIO = 100
_DOCX_MAX_XML_PART_BYTES = 25 * 1024 * 1024
_DOCX_MAIN_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"

IMAGE_MAX_PIXELS = 50_000_000

FFPROBE_TIMEOUT_SECONDS = 10
FFPROBE_CPU_LIMIT_SECONDS = 10
FFPROBE_MEMORY_LIMIT_BYTES = 512 * 1024 * 1024


def _reject(detail: str = "Attachment content does not match extension") -> UnsupportedAttachmentContent:
    return UnsupportedAttachmentContent(detail)


# ---------------------------------------------------------------- PDF


def _validate_pdf(path: Path) -> None:
    try:
        reader = PdfReader(str(path), strict=True)
        if reader.is_encrypted:
            raise _reject("Encrypted PDF attachments are not allowed")
        if len(reader.pages) < 1:
            raise _reject()
    except UnsupportedAttachmentContent:
        raise
    except Exception as exc:
        raise _reject() from exc


# ---------------------------------------------------------------- DOC


_DOC_MACRO_STORAGES = {"macros", "_vba_project_cur", "vba", "_vba_project"}


def _validate_doc(path: Path) -> None:
    try:
        if not olefile.isOleFile(str(path)):
            raise _reject()
        with olefile.OleFileIO(str(path)) as ole:
            if not ole.exists("WordDocument"):
                raise _reject()
            entries = ole.listdir(streams=True, storages=True)
    except UnsupportedAttachmentContent:
        raise
    except Exception as exc:
        raise _reject() from exc

    for entry in entries:
        if any(part.lower() in _DOC_MACRO_STORAGES for part in entry):
            raise _reject("DOC attachments with macros/VBA are not allowed")


# ---------------------------------------------------------------- DOCX


_DOCX_CONTENT_TYPES_PART = "[Content_Types].xml"
_DOCX_PACKAGE_RELS_PART = "_rels/.rels"
_DOCX_MAIN_PART = "word/document.xml"

_OPC_CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_OPC_RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
# WordprocessingML transitional (ECMA-376) e strict (ISO/IEC 29500 strict).
_WORDML_NAMESPACES = frozenset(
    {
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://purl.oclc.org/ooxml/wordprocessingml/main",
    }
)
_OFFICE_DOCUMENT_REL_TYPES = frozenset(
    {
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        "http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument",
    }
)
# marcadores de macro/VBA em Content-Type e em tipo de relacionamento: valem mesmo
# quando a parte foi renomeada (o nome vbaProject.bin não é a única prova).
_DOCX_MACRO_CONTENT_TYPE_MARKERS = ("macroenabled", "vbaproject", "vbadata")
_DOCX_MACRO_REL_TYPE_MARKERS = ("vbaproject", "vbadata")


def _is_vba_project_entry(filename: str) -> bool:
    # vbaProject.bin em qualquer pasta do pacote, independentemente de capitalização,
    # separador ("\" ou "/") ou ponto/espaço final; o Content-Type declarado é irrelevante.
    basename = filename.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    return basename.rstrip(" .").casefold() == "vbaproject.bin"


def _normalized_part_name(filename: str) -> str:
    # nomes de parte OPC são case-insensitive: "Word/Document.xml" colide com
    # "word/document.xml".
    return filename.replace("\\", "/").lstrip("/").casefold()


def _is_kept_xml_part(filename: str) -> bool:
    return filename in (_DOCX_CONTENT_TYPES_PART, _DOCX_MAIN_PART) or filename.endswith(".rels")


def _read_all_docx_members(zf: zipfile.ZipFile, infos: list[zipfile.ZipInfo]) -> dict[str, bytes]:
    # Lê integralmente todos os membros para que o zipfile confira o CRC-32 de cada um
    # (BadZipFile em divergência). O total real lido é limitado — o tamanho declarado
    # no cabeçalho não é confiável. Só as partes XML necessárias ficam em memória.
    kept: dict[str, bytes] = {}
    total_read = 0
    for info in infos:
        keep = _is_kept_xml_part(info.filename)
        chunks: list[bytes] = []
        part_size = 0
        with zf.open(info) as fh:
            while True:
                chunk = fh.read(_READ_CHUNK_BYTES)
                if not chunk:
                    break
                total_read += len(chunk)
                part_size += len(chunk)
                if total_read > DOCX_MAX_UNCOMPRESSED_BYTES:
                    raise _reject("DOCX attachment exceeds archive limits")
                if keep:
                    if part_size > _DOCX_MAX_XML_PART_BYTES:
                        raise _reject()
                    chunks.append(chunk)
        if keep:
            kept[info.filename] = b"".join(chunks)
    return kept


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _check_root(root, namespaces: frozenset[str], local_name: str) -> None:
    if not root.tag.startswith("{"):
        raise _reject()
    namespace, _, name = root.tag[1:].partition("}")
    if namespace not in namespaces or name != local_name:
        raise _reject()


def _validate_docx(path: Path) -> None:
    try:
        if not zipfile.is_zipfile(path):
            raise _reject()
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            if len(infos) > DOCX_MAX_ENTRIES:
                raise _reject("DOCX attachment exceeds archive limits")

            total_uncompressed = sum(info.file_size for info in infos)
            total_compressed = sum(info.compress_size for info in infos)
            if total_uncompressed > DOCX_MAX_UNCOMPRESSED_BYTES:
                raise _reject("DOCX attachment exceeds archive limits")
            if total_uncompressed > DOCX_MAX_COMPRESSION_RATIO * max(total_compressed, 1):
                raise _reject("DOCX attachment exceeds archive limits")
            seen_names: set[str] = set()
            for info in infos:
                if _is_vba_project_entry(info.filename):
                    raise _reject("Macro-enabled DOCX attachments are not allowed")
                if info.flag_bits & 0x1:
                    raise _reject()
                if info.file_size > DOCX_MAX_COMPRESSION_RATIO * max(info.compress_size, 1):
                    raise _reject("DOCX attachment exceeds archive limits")
                # nome duplicado (exato ou só por capitalização/separador) torna ambígua
                # a parte efetivamente lida por cada consumidor → rejeita.
                normalized = _normalized_part_name(info.filename)
                if normalized in seen_names:
                    raise _reject()
                seen_names.add(normalized)

            parts = _read_all_docx_members(zf, infos)
    except UnsupportedAttachmentContent:
        raise
    except Exception as exc:
        raise _reject() from exc

    for required in (_DOCX_CONTENT_TYPES_PART, _DOCX_PACKAGE_RELS_PART, _DOCX_MAIN_PART):
        if required not in parts:
            raise _reject()

    try:
        content_types = SafeElementTree.fromstring(parts[_DOCX_CONTENT_TYPES_PART])
        package_rels = SafeElementTree.fromstring(parts[_DOCX_PACKAGE_RELS_PART])
        document = SafeElementTree.fromstring(parts[_DOCX_MAIN_PART])
        other_rels = [
            SafeElementTree.fromstring(data)
            for name, data in parts.items()
            if name.endswith(".rels") and name != _DOCX_PACKAGE_RELS_PART
        ]
    except Exception as exc:
        raise _reject() from exc

    _check_root(content_types, frozenset({_OPC_CONTENT_TYPES_NS}), "Types")
    _check_root(package_rels, frozenset({_OPC_RELATIONSHIPS_NS}), "Relationships")
    _check_root(document, _WORDML_NAMESPACES, "document")
    for rels in other_rels:
        _check_root(rels, frozenset({_OPC_RELATIONSHIPS_NS}), "Relationships")

    declared_types = []
    for element in content_types.iter():
        if _local_name(element.tag) not in ("Default", "Override"):
            continue
        content_type = element.get("ContentType") or ""
        if any(marker in content_type.casefold() for marker in _DOCX_MACRO_CONTENT_TYPE_MARKERS):
            raise _reject("Macro-enabled DOCX attachments are not allowed")
        if _local_name(element.tag) == "Override":
            declared_types.append((element.get("PartName") or "", content_type))
    if ("/word/document.xml", _DOCX_MAIN_CONTENT_TYPE) not in declared_types:
        raise _reject()

    for rels in (package_rels, *other_rels):
        for relationship in rels.iter():
            if _local_name(relationship.tag) != "Relationship":
                continue
            rel_type = (relationship.get("Type") or "").casefold()
            if any(marker in rel_type for marker in _DOCX_MACRO_REL_TYPE_MARKERS):
                raise _reject("Macro-enabled DOCX attachments are not allowed")

    office_documents = [
        relationship
        for relationship in package_rels.iter()
        if _local_name(relationship.tag) == "Relationship"
        and relationship.get("Type") in _OFFICE_DOCUMENT_REL_TYPES
    ]
    if len(office_documents) != 1:
        raise _reject()
    office_document = office_documents[0]
    if (office_document.get("TargetMode") or "Internal") != "Internal":
        raise _reject()
    if (office_document.get("Target") or "").lstrip("/") != _DOCX_MAIN_PART:
        raise _reject()


# ---------------------------------------------------------------- TXT


def _validate_txt(path: Path) -> None:
    # UTF-8 estrito (BOM aceito); controles binários fora de TAB/LF/FF/CR rejeitados,
    # o que também rejeita UTF-16/32 sem BOM.
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    try:
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(_READ_CHUNK_BYTES)
                if not chunk:
                    decoder.decode(b"", final=True)
                    return
                if any(b < 0x20 and b not in (0x09, 0x0A, 0x0C, 0x0D) for b in chunk):
                    raise _reject("TXT attachments must be UTF-8 text")
                decoder.decode(chunk)
    except UnicodeDecodeError as exc:
        raise _reject("TXT attachments must be UTF-8 text") from exc


# ---------------------------------------------------------------- imagens


def _validate_image(path: Path, expected_format: str) -> None:
    try:
        with Image.open(path) as img:
            if img.format != expected_format:
                raise _reject()
            width, height = img.size
            if width < 1 or height < 1 or width * height > IMAGE_MAX_PIXELS:
                raise _reject("Image attachment exceeds pixel limit")
            img.verify()
        # verify() invalida o objeto; reabrir para decodificar de fato.
        with Image.open(path) as img:
            if img.format != expected_format or img.size != (width, height):
                raise _reject()
            img.load()
    except UnsupportedAttachmentContent:
        raise
    except Exception as exc:
        # inclui Image.DecompressionBombError
        raise _reject() from exc


# ---------------------------------------------------------------- mídia


# demuxers aceitos por extensão (format_name do ffprobe)
_MP4_FAMILY = "mov,mp4,m4a,3gp,3g2,mj2"
_MEDIA_DEMUXERS = {
    ".mp3": "mp3",
    ".wav": "wav",
    ".m4a": _MP4_FAMILY,
    ".mp4": _MP4_FAMILY,
    ".mov": _MP4_FAMILY,
    ".webm": "matroska,webm",
}

# Rejeição preventiva de 3GP/3GP2 em .mp4/.mov/.m4a (Opção B): o demuxer da família
# MP4 é o mesmo para 3GP, então todo major_brand iniciado por "3g" ("3gp4", "3g2a"...)
# é rejeitado independentemente do codec. É critério só de rejeição, não prova de
# formato: reescrita da marca no ftyp ou remux (ex.: -c copy para MP4) contornam-no
# (limitação registrada).
_3GP_BRAND_PREFIX = "3g"

# Shell POSIX usado apenas como wrapper de limites (sem shell=True e sem interpolar
# entrada do usuário): o script é fixo e os argumentos chegam como argv ("$0" "$@").
_LIMIT_SHELL = "/bin/sh"
# Validador ausente/não executável sob o wrapper: 126 (ulimit falhou ou exec sem
# permissão) e 127 (binário não encontrado) → indisponível (503), nunca aceito.
_WRAPPER_UNAVAILABLE_CODES = frozenset({126, 127})


def _limited_command(binary: str, args: list[str]) -> list[str]:
    # ulimit -v usa KiB: 524288 KiB = 512 MiB. Falha ao aplicar qualquer limite → 126.
    script = (
        f"ulimit -t {FFPROBE_CPU_LIMIT_SECONDS} || exit 126; "
        f"ulimit -v {FFPROBE_MEMORY_LIMIT_BYTES // 1024} || exit 126; "
        'exec "$0" "$@"'
    )
    return [_LIMIT_SHELL, "-c", script, binary, *args]


def _run_limited(binary: str, args: list[str]) -> subprocess.CompletedProcess:
    try:
        completed = subprocess.run(
            _limited_command(binary, args),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=FFPROBE_TIMEOUT_SECONDS,
            check=False,
            close_fds=True,
        )
    except FileNotFoundError as exc:
        raise AttachmentValidatorUnavailable("Media validator unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise _reject() from exc
    except Exception as exc:
        raise _reject() from exc

    if completed.returncode in _WRAPPER_UNAVAILABLE_CODES:
        raise AttachmentValidatorUnavailable("Media validator unavailable")
    # código não zero (inclusive morte por sinal, ex.: limite de CPU) ou qualquer
    # diagnóstico em stderr (com -v error) → fail-closed.
    if completed.returncode != 0 or (completed.stderr or b"").strip():
        raise _reject()
    return completed


def _is_attached_picture(stream: dict) -> bool:
    disposition = stream.get("disposition") or {}
    return stream.get("codec_type") == "video" and disposition.get("attached_pic") == 1


def _check_media_streams(suffix: str, streams: list, major_brand: str) -> None:
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    has_video = any(stream.get("codec_type") == "video" and not _is_attached_picture(stream) for stream in streams)

    if suffix == ".m4a":
        # áudio obrigatório; vídeo só como capa (disposition.attached_pic=1).
        if not has_audio or has_video:
            raise _reject()
    elif suffix in (".mp4", ".mov"):
        if not (has_audio or has_video):
            raise _reject()
    elif not any(stream.get("codec_type") in ("audio", "video") for stream in streams):
        raise _reject()

    if _MEDIA_DEMUXERS[suffix] == _MP4_FAMILY and major_brand.strip().lower().startswith(_3GP_BRAND_PREFIX):
        raise _reject()


def _validate_media(path: Path, suffix: str) -> None:
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if ffprobe is None or ffmpeg is None:
        raise AttachmentValidatorUnavailable("Media validator unavailable")

    demuxers = _MEDIA_DEMUXERS[suffix]
    source = f"file:{path}"
    completed = _run_limited(
        ffprobe,
        [
            "-v", "error",
            "-protocol_whitelist", "file",
            "-format_whitelist", demuxers,
            "-show_entries",
            "format=format_name:format_tags=major_brand"
            ":stream=codec_type,codec_name:stream_disposition=attached_pic",
            "-of", "json",
            source,
        ],
    )

    try:
        probe = json.loads(completed.stdout or b"{}")
        format_name = probe["format"]["format_name"]
        major_brand = str((probe["format"].get("tags") or {}).get("major_brand") or "")
        streams = probe.get("streams") or []
        if not all(isinstance(stream, dict) for stream in streams):
            raise _reject()
    except UnsupportedAttachmentContent:
        raise
    except Exception as exc:
        raise _reject() from exc

    if format_name != demuxers:
        raise _reject()
    _check_media_streams(suffix, streams, major_brand)

    # passagem completa: demuxa todos os pacotes de todos os streams (sem decodificar)
    # e aborta no primeiro erro (-xerror). Detecta contêiner truncado/corrompido que o
    # ffprobe aceita; não garante a integridade do payload de áudio/vídeo.
    _run_limited(
        ffmpeg,
        [
            "-nostdin",
            "-v", "error",
            "-xerror",
            "-protocol_whitelist", "file",
            "-format_whitelist", demuxers,
            "-i", source,
            "-map", "0",
            "-c", "copy",
            "-f", "null",
            "-",
        ],
    )


# ---------------------------------------------------------------- entrada


_IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def validate_attachment_content(path: Path, suffix: str) -> None:
    """Valida o arquivo gravado em ``path`` para a extensão já normalizada ``suffix``.

    Levanta ``UnsupportedAttachmentContent`` (415) ou
    ``AttachmentValidatorUnavailable`` (503). Retorna ``None`` se válido.
    """
    if suffix == ".pdf":
        _validate_pdf(path)
    elif suffix == ".doc":
        _validate_doc(path)
    elif suffix == ".docx":
        _validate_docx(path)
    elif suffix == ".txt":
        _validate_txt(path)
    elif suffix in _IMAGE_FORMATS:
        _validate_image(path, _IMAGE_FORMATS[suffix])
    elif suffix in _MEDIA_DEMUXERS:
        _validate_media(path, suffix)
    else:
        raise _reject("Unsupported attachment format")
