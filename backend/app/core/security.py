import time
from typing import Literal

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
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


def require_auth(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if not settings.AUTH_ENABLED:
        set_tenant_on_session(db, 1)
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
