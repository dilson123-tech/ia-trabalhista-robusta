from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import select, inspect, Table, MetaData
from sqlalchemy.exc import IntegrityError

import datetime as _dt
import re
import zlib

from app.core.settings import settings
from app.core.security import issue_token, require_auth, require_role, pwd_context
from app.db.session import get_db
from app.core.tenant import set_tenant_on_session
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.auth import LoginIn, TokenOut, UserOut, SeedAdminIn, ChangePasswordIn

router = APIRouter(prefix="/auth", tags=["auth"])

def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s[:48] or "tenant")


def _fallback_tid(username: str) -> int:
    # int estável (sem depender de tabela tenants)
    v = zlib.crc32(username.encode("utf-8")) & 0x7FFFFFFF
    return int(v or 1)


def _ensure_tenant_id(db: Session, username: str) -> int:
    bind = db.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names() or [])
    if "tenants" not in tables:
        return _fallback_tid(username)

    md = MetaData()
    tenants = Table("tenants", md, autoload_with=bind)

    # pega PK e tenta reutilizar um tenant existente (DX + menos lixo)
    pk_cols = [c for c in tenants.columns if c.primary_key]
    pk = pk_cols[0] if pk_cols else tenants.columns[list(tenants.columns.keys())[0]]
    # RLS FORCE pode esconder/impedir INSERT em tenants.
    # Estratégia: define app.tenant_id=1 (tenant dev padrão) e reutiliza um tenant existente.
    try:
        set_tenant_on_session(db, 1)
    except Exception:
        pass

    try:
        row0 = db.execute(select(pk).limit(1)).first()
        if row0 and row0[0] is not None:
            return int(row0[0])
    except Exception:
        pass


    
    cols = {c.name: c for c in tenants.columns}
    payload: dict = {}

    # campos comuns
    if "name" in cols:
        payload["name"] = f"Tenant {username}"
    elif "title" in cols:
        payload["title"] = f"Tenant {username}"
    if "slug" in cols:
        payload["slug"] = _slugify(username)
    elif "code" in cols:
        payload["code"] = _slugify(username)

    # completar colunas NOT NULL sem default (best-effort seguro)
    for c in tenants.columns:
        if c.primary_key or c.name in payload:
            continue
        if c.nullable or c.default is not None or c.server_default is not None:
            continue

        if c.name in ("created_at", "created"):
            payload[c.name] = _dt.datetime.utcnow()
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
                raise HTTPException(
                    status_code=500,
                    detail=f"cannot auto-provision tenant: required column '{c.name}' needs a value",
                )

    res = db.execute(tenants.insert().values(**payload))
    db.commit()

    new_id = None
    try:
        new_id = res.inserted_primary_key[0]
    except Exception:
        new_id = None

    if new_id is None and "slug" in payload and "slug" in cols and "id" in cols:
        row2 = db.execute(select(tenants.c.id).where(tenants.c.slug == payload["slug"])).first()
        if row2:
            new_id = row2[0]

    if new_id is None:
        raise HTTPException(status_code=500, detail="cannot determine new tenant id")

    return int(new_id)


def _ensure_membership(db: Session, u: User) -> TenantMember:
    m = db.execute(select(TenantMember).where(TenantMember.user_id == u.id)).scalar_one_or_none()
    if m is not None:
        return m

    tenant_id = _ensure_tenant_id(db, u.username)
    # RLS FORCE: operar como tenant alvo para inserts/updates
    set_tenant_on_session(db, tenant_id)
    exp = _dt.datetime.utcnow() + _dt.timedelta(days=30)
    db.execute(
        text(
            "INSERT INTO subscriptions (tenant_id, plan_type, status, case_limit, active, expires_at) "
            "VALUES (:tid, 'basic', 'trial', :case_limit, :active, :exp) "
            "ON CONFLICT (tenant_id) DO NOTHING"
        ),
        {"tid": tenant_id, "case_limit": 10, "active": True, "exp": exp},
    )


    cols = set(TenantMember.__table__.columns.keys())
    data: dict = {}

    if "tenant_id" in cols:
        data["tenant_id"] = tenant_id
    elif "tid" in cols:
        data["tid"] = tenant_id
    else:
        raise HTTPException(status_code=500, detail="tenant member missing tenant_id column")

    if "user_id" in cols:
        data["user_id"] = u.id
    else:
        raise HTTPException(status_code=500, detail="tenant member missing user_id column")

    if "role" in cols:
        data["role"] = getattr(u, "role", "user")
    elif "member_role" in cols:
        data["member_role"] = getattr(u, "role", "user")

    if "is_owner" in cols:
        data["is_owner"] = True if getattr(u, "role", "") == "admin" else False

    m = TenantMember(**data)
    db.add(m)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        m = db.execute(select(TenantMember).where(TenantMember.user_id == u.id)).scalar_one()
        return m

    db.refresh(m)
    return m



@router.post("/seed-admin")
def seed_admin(
    payload: SeedAdminIn,
    x_seed_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
        # HARDENING: seed-admin é break-glass (desativado por padrão)
    if not settings.ALLOW_SEED_ADMIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    if not settings.ADMIN_SEED_TOKEN or settings.ADMIN_SEED_TOKEN == "CHANGE_ME_SEED_TOKEN":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="seed token not configured")

    if x_seed_token != settings.ADMIN_SEED_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid seed token")

    existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if existing:
        _ensure_membership(db, existing)
        return {"ok": True, "seeded": False, "reason": "already exists"}

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

    db.refresh(u)
    _ensure_membership(db, u)

    return {"ok": True, "seeded": True, "username": payload.username, "role": payload.role}



@router.post("/users", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def create_user(payload: SeedAdminIn, db: Session = Depends(get_db)):
    """
    Cria usuário (admin-only).
    Reaproveita SeedAdminIn: {username,password,role}.
    """
    existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")
    db.refresh(u)
    return UserOut(username=u.username, role=u.role)







@router.patch("/users/{user_id}/activate", dependencies=[Depends(require_role("admin"))])
def activate_user(user_id: int, db: Session = Depends(get_db)):
    """
    Admin do tenant ativa um usuário (is_active=True).
    """
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    u.is_active = True
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"username": u.username, "role": u.role, "is_active": u.is_active}


@router.patch("/users/{user_id}/deactivate", dependencies=[Depends(require_role("admin"))])
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    Admin do tenant desativa um usuário (is_active=False).
    """
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    u.is_active = False
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"username": u.username, "role": u.role, "is_active": u.is_active}


@router.get("/users", dependencies=[Depends(require_role("admin"))])
def list_users(claims=Depends(require_auth), db: Session = Depends(get_db)):
    """
    Lista usuários do tenant atual (admin-only).
    Retorna somente usuários com membership no tenant do token.
    """
    tenant_id = claims.get("tenant_id")
    rows = db.execute(
        select(User.id, User.username, User.role, User.is_active)
        .join(TenantMember, TenantMember.user_id == User.id)
        .where(TenantMember.tenant_id == tenant_id)
        .order_by(User.id)
    ).all()

    return [
        {"id": r.id, "username": r.username, "role": r.role, "is_active": r.is_active}
        for r in rows
    ]


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    u = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()

    if (u is None) or (not pwd_context.verify(payload.password, u.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bad credentials",
        )

    if not u.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is inactive",
        )

    membership = db.execute(
        select(TenantMember).where(TenantMember.user_id == u.id)
    ).scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=403, detail="no tenant membership")

    token = issue_token(u.username, u.role, membership.tenant_id)
    return TokenOut(access_token=token)

@router.post("/me/password")
def change_my_password(
    payload: ChangePasswordIn,
    claims=Depends(require_auth),
    db: Session = Depends(get_db),
):
    username = (claims or {}).get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    u = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if (u is None) or (not pwd_context.verify(payload.old_password, u.password_hash)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")

    if payload.old_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="new password must differ")

    if len(payload.new_password or "") < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password too short (min 8)")

    u.password_hash = pwd_context.hash(payload.new_password)
    db.add(u)
    db.commit()
    return {"ok": True}


@router.get("/whoami", response_model=UserOut)
def whoami(claims=Depends(require_auth)):
    return UserOut(username=claims.get("sub", "?"), role=claims.get("role", "?"))


@router.get("/admin-only")
def admin_only(_=Depends(require_role("admin"))):
    return {"ok": True, "admin": True}
