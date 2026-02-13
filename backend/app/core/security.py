from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Callable, Literal, Optional, Set, Dict, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.settings import settings

# -----------------------------------------------------------------------------
# Hardening: bcrypt direto (sem passlib/crypt), compatível com Python 3.13+
# Mantém a API antiga do projeto (issue_token/require_auth/require_role/pwd_context)
# para não quebrar rotas e testes.
# -----------------------------------------------------------------------------

UserRole = Literal["admin", "advogado", "estagiario", "leitura"]
ROLES: Set[UserRole] = {"admin", "advogado", "estagiario", "leitura"}

BCRYPT_ROUNDS = 12  # 10-14 comum; 12 é um bom default.
_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    pw = password.encode("utf-8")
    h = bcrypt.hashpw(pw, bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    return h.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False

class _PwdContextCompat:
    # drop-in compat para código que fazia pwd_context.hash/verify
    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

pwd_context = _PwdContextCompat()

def issue_token(username: str, role: UserRole) -> str:
    if role not in ROLES:
        raise HTTPException(status_code=400, detail="invalid role")

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=int(getattr(settings, "JWT_EXPIRES_MIN", 60) or 60))

    claims = {
        "sub": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    secret = getattr(settings, "JWT_SECRET", None) or getattr(settings, "AUTH_JWT_SECRET", None)
    alg = getattr(settings, "JWT_ALG", None) or getattr(settings, "AUTH_JWT_ALG", None) or "HS256"

    if not secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    return jwt.encode(claims, secret, algorithm=alg)

def require_auth(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Dict[str, Any]:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="missing token")

    token = creds.credentials
    secret = getattr(settings, "JWT_SECRET", None) or getattr(settings, "AUTH_JWT_SECRET", None)
    alg = getattr(settings, "JWT_ALG", None) or getattr(settings, "AUTH_JWT_ALG", None) or "HS256"

    if not secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")

    try:
        claims = jwt.decode(token, secret, algorithms=[alg])
        # sanity mínima
        if "sub" not in claims or "role" not in claims:
            raise HTTPException(status_code=401, detail="invalid token")
        return claims
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")

def require_role(*allowed_roles: UserRole) -> Callable[..., Dict[str, Any]]:
    allowed: Set[UserRole] = set(allowed_roles)

    def _dep(claims: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        role = claims.get("role")
        if allowed and role not in allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return claims

    return _dep
