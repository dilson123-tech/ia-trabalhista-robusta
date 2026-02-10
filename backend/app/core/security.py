import time
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.settings import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

# "DB" in-memory por enquanto (robusto depois com Postgres)
_USERS = {}  # username -> {password_hash, role}

ROLES = {"admin", "advogado", "estagiario", "leitura"}

def create_user(username: str, password: str, role: str):
    if role not in ROLES:
        raise ValueError("invalid role")
    _USERS[username] = {
        "password_hash": pwd_context.hash(password),
        "role": role,
    }

def verify_user(username: str, password: str) -> bool:
    u = _USERS.get(username)
    if not u:
        return False
    return pwd_context.verify(password, u["password_hash"])

def issue_token(username: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + settings.JWT_EXPIRES_MIN * 60,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

def require_auth(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if not settings.AUTH_ENABLED:
        return {"sub": "dev", "role": "admin"}
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    return decode_token(creds.credentials)

def require_role(*allowed):
    def dep(claims=Depends(require_auth)):
        if not allowed:
            return claims
        if claims.get("role") not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return claims
    return dep
