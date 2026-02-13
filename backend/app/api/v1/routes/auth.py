from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.settings import get_settings
from app.core.security import issue_token, require_auth, require_role, pwd_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn, TokenOut, UserOut, SeedAdminIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/seed-admin")
def seed_admin(
    payload: SeedAdminIn,
    x_seed_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if x_seed_token != get_settings().ADMIN_SEED_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid seed token")

    existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if existing:
        existing.password_hash = pwd_context.hash(payload.password)
        existing.role = payload.role
        db.add(existing)
        db.commit()
        return {"ok": True, "seeded": True, "updated": True, "username": payload.username, "role": payload.role}

    u = User(
        username=payload.username,
        password_hash=pwd_context.hash(payload.password),
        role=payload.role,
    )
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"ok": True, "seeded": False, "reason": "already exists"}

    return {"ok": True, "seeded": True, "username": payload.username, "role": payload.role}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    u = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if (u is None) or (not pwd_context.verify(payload.password, u.password_hash)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")

    token = issue_token(u.username, u.role)
    return TokenOut(access_token=token)


@router.get("/whoami", response_model=UserOut)
def whoami(claims=Depends(require_auth)):
    return UserOut(username=claims.get("sub", "?"), role=claims.get("role", "?"))


@router.get("/admin-only")
def admin_only(_=Depends(require_role("admin"))):
    return {"ok": True, "admin": True}
