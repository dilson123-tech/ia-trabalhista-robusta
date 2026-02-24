import time
from typing import Literal

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy import select, inspect, Table, MetaData
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.tenant import set_tenant_on_session
from app.db.session import get_db

UserRole = Literal["admin", "advogado", "estagiario", "leitura"]

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

ROLES: set[UserRole] = {"admin", "advogado", "estagiario", "leitura"}


def issue_token(username: str, role: UserRole, tenant_id: int) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "role": role,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + settings.JWT_EXPIRES_MIN * 60,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )



def _ensure_dev_tenant(db: "Session", tenant_id: int = 1) -> None:
    """
    DEV/CI bootstrap:
    garante que exista tenants.id=tenant_id para não quebrar FK do usage_counters
    quando AUTH_ENABLED=false (tenant fixo).
    Respeita RLS porque o caller já setou app.tenant_id.
    """
    bind = db.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names() or [])
    if "tenants" not in tables:
        return

    md = MetaData()
    tenants = Table("tenants", md, autoload_with=bind)

    # já existe?
    row = db.execute(select(tenants.c.id).where(tenants.c.id == tenant_id)).first()
    if row:
        return

    cols = {c.name: c for c in tenants.columns}
    payload: dict = {}

    if "id" in cols:
        payload["id"] = tenant_id
    if "name" in cols:
        payload["name"] = f"Tenant {tenant_id}"
    if "slug" in cols:
        payload["slug"] = f"tenant-{tenant_id}"
    elif "code" in cols:
        payload["code"] = f"tenant-{tenant_id}"

    # completa NOT NULL sem default (best-effort)
    for c in tenants.columns:
        if c.primary_key or c.name in payload:
            continue
        if c.nullable or c.default is not None or c.server_default is not None:
            continue

        if c.name in ("created_at", "created"):
            payload[c.name] = datetime.now(timezone.utc)
        elif c.name in ("is_active", "active", "enabled"):
            payload[c.name] = True
        else:
            py = getattr(c.type, "python_type", None)
            if py is str:
                payload[c.name] = ""
            elif py is int:
                payload[c.name] = 0
            elif py is bool:
                payload[c.name] = True
            else:
                payload[c.name] = None

    db.execute(tenants.insert().values(**payload))

def require_auth(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if not settings.AUTH_ENABLED:
        set_tenant_on_session(db, 1)
        _ensure_dev_tenant(db, 1)
        return {"sub": "dev", "role": "admin", "tenant_id": 1}

    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing token",
        )

    claims = decode_token(creds.credentials)

    tenant_id = claims.get("tenant_id")
    user = db.execute(text("SELECT id FROM users WHERE username = :u"), {"u": claims.get("sub")}).fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    member = db.execute(text("SELECT 1 FROM tenant_members WHERE user_id = :uid AND tenant_id = :tid"), {"uid": user[0], "tid": tenant_id}).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid tenant membership")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="tenant missing",
        )

    set_tenant_on_session(db, tenant_id)

    return claims


def require_role(*allowed: UserRole):
    def dep(claims=Depends(require_auth)):
        if not allowed:
            return claims

        if claims.get("role") not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="forbidden",
            )

        return claims

    return dep
