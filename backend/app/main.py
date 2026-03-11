from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import text as sql_text
from app.db.session import SessionLocal

import logging
import re
import time
from app.core.middleware import install_middleware
from app.core.settings import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.api.v1.router import api_router

setup_logging(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)

# Garantia: audit middleware sempre ativo

# Middleware padrão (request_id, tempo, audit no Postgres)
install_middleware(app)

admin_audit_logger = logging.getLogger("admin_audit")

# Audit trail de suporte (somente /api/v1/admin/*)
@app.middleware("http")
async def admin_audit_middleware(request: Request, call_next):
    path = request.url.path
    admin_prefix = f"{settings.API_V1_PREFIX}/admin"
    if not path.startswith(admin_prefix):
        return await call_next(request)

    t0 = time.perf_counter()

    # NÃO logar X-Admin-Key (segredo). Só actor opcional.
    actor = request.headers.get("X-Admin-Actor") or request.headers.get("x-admin-actor")

    # tenta extrair tenant_id do path: /api/v1/admin/tenants/{id}/...
    m = re.search(r"/admin/tenants/(\d+)", path)
    tenant_id = int(m.group(1)) if m else None

    # request_id (se já existir no contexto/header)
    rid = (
        request.headers.get("X-Request-Id")
        or request.headers.get("X-Request-ID")
        or getattr(getattr(request, "state", None), "request_id", None)
        or getattr(getattr(request, "state", None), "requestId", None)
    )

    status_code = None
    try:
        resp = await call_next(request)
        status_code = resp.status_code
        return resp
    finally:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        # log enxuto e auditável
        admin_audit_logger.info(
            "admin_audit actor=%s tenant_id=%s method=%s path=%s status=%s duration_ms=%s request_id=%s",
            actor,
            tenant_id,
            request.method,
            path,
            status_code,
            dt_ms,
            rid,
        )

app.add_middleware(RequestContextMiddleware)

# health “raiz” (ops rápido)
@app.get("/health", tags=["ops"])
def health():
    return {
        "ok": True,
        "service": "ia_trabalhista_robusta",
        "env": settings.APP_ENV,
        "version": "0.1.0",
    }

@app.get("/ready", tags=["ops"])
def ready():
    db = SessionLocal()
    try:
        db.execute(sql_text("SELECT 1"))
        return {
            "ok": True,
            "service": "ia_trabalhista_robusta",
            "env": settings.APP_ENV,
            "version": "0.1.0",
            "database": "ok",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "ok": False,
                "service": "ia_trabalhista_robusta",
                "env": settings.APP_ENV,
                "version": "0.1.0",
                "database": "error",
                "reason": str(e),
            },
        )
    finally:
        db.close()

# API versionada
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
