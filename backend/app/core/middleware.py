from __future__ import annotations

import time
import uuid
from typing import Iterable, Tuple

import anyio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.settings import settings
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog

_DEFAULT_EXCLUDE: Tuple[str, ...] = (
    "/api/v1/health",
    "/openapi.json",
    "/docs",
    "/docs/",
    "/redoc",
    "/redoc/",
    "/favicon.ico",
)

def _get_excludes() -> set[str]:
    val = getattr(settings, "AUDIT_EXCLUDE_PATHS", None)
    if not val:
        return set(_DEFAULT_EXCLUDE)
    if isinstance(val, (list, tuple, set)):
        return set(str(x).strip() for x in val if str(x).strip())
    if isinstance(val, str):
        return set(s.strip() for s in val.split(",") if s.strip())
    return set(_DEFAULT_EXCLUDE)

def _extract_identity(request: Request) -> Tuple[str, str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return "", ""
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return "", ""

    # tenta decodificar JWT (se PyJWT estiver instalado e tiver secret)
    try:
        import jwt  # type: ignore
        secret = getattr(settings, "JWT_SECRET", "") or getattr(settings, "AUTH_JWT_SECRET", "")
        if not secret:
            return "", ""
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        sub = payload.get("sub") or ""
        role = payload.get("role") or ""
        return str(sub), str(role)
    except Exception:
        return "", ""

def _write_audit(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    username: str,
    role: str,
    process_time_ms: float,
) -> None:
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                username=username or "",
                role=role or "",
                process_time_ms=process_time_ms,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

class RequestAuditMiddleware(BaseHTTPMiddleware):
    """Middleware de auditoria + contexto.
    - Sempre adiciona headers: x-request-id, x-process-time-ms (quando há response)
    - Loga em audit_logs (best-effort: se der erro no DB, não derruba request)
    """

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id

        start = time.perf_counter()
        response: Response | None = None
        status_code = 500
        path = request.url.path
        method = request.method
        excludes = _get_excludes()

        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 200) or 200
            return response
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            # headers de contexto (só se tiver response)
            if response is not None:
                response.headers["x-request-id"] = request_id
                response.headers["x-process-time-ms"] = f"{elapsed_ms:.2f}"

            # audit best-effort
            if path not in excludes:
                username, role = _extract_identity(request)
                await anyio.to_thread.run_sync(
                    _write_audit,
                    request_id,
                    method,
                    path,
                    int(status_code),
                    username,
                    role,
                    float(elapsed_ms),
                )

# compat: código antigo pode importar RequestContextMiddleware
class RequestContextMiddleware(RequestAuditMiddleware):
    pass
# ---- Backward-compat -------------------------------------------------
# main.py antigo importava install_middleware()
def install_middleware(app):
    """Backward-compat: install RequestAuditMiddleware (idempotent)."""
    try:
        for m in getattr(app, "user_middleware", []):
            if getattr(m, "cls", None) is RequestAuditMiddleware:
                return
    except Exception:
        pass
    app.add_middleware(RequestAuditMiddleware)
