from __future__ import annotations

import threading

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from app.core.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AdminDatabaseNotConfigured(RuntimeError):
    """ADMIN_DATABASE_URL ausente ou inválida. Mensagem nunca contém a URL."""


_admin_lock = threading.Lock()
_admin_engine: Engine | None = None
_admin_sessionmaker: sessionmaker | None = None


def _admin_database_url() -> str:
    url = (settings.ADMIN_DATABASE_URL or "").strip()
    if not url:
        raise AdminDatabaseNotConfigured("ADMIN_DATABASE_URL is not configured")
    runtime = (settings.DATABASE_URL or "").strip()
    if url == runtime:
        raise AdminDatabaseNotConfigured("ADMIN_DATABASE_URL must differ from DATABASE_URL")
    try:
        admin_u = make_url(url)
        runtime_u = make_url(runtime)
    except Exception:
        raise AdminDatabaseNotConfigured("ADMIN_DATABASE_URL is invalid") from None
    # Mesma role no mesmo banco equivale à mesma credencial: não é uma conexão admin separada.
    if (admin_u.username, admin_u.host, admin_u.port, admin_u.database) == (
        runtime_u.username,
        runtime_u.host,
        runtime_u.port,
        runtime_u.database,
    ):
        raise AdminDatabaseNotConfigured("ADMIN_DATABASE_URL must use a role distinct from DATABASE_URL")
    return url


def AdminSessionLocal() -> Session:
    """
    Sessão da conexão administrativa (role membro de ia_rls_admin).
    Sem fallback para DATABASE_URL: falha fechado se não configurada.
    """
    global _admin_engine, _admin_sessionmaker
    if _admin_sessionmaker is None:
        with _admin_lock:
            if _admin_sessionmaker is None:
                url = _admin_database_url()
                try:
                    _admin_engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)
                except Exception:
                    # Não propagar a mensagem original: pode conter a URL/credencial.
                    raise AdminDatabaseNotConfigured("ADMIN_DATABASE_URL is invalid") from None
                _admin_sessionmaker = sessionmaker(
                    autocommit=False, autoflush=False, bind=_admin_engine, expire_on_commit=False
                )
    return _admin_sessionmaker()


def get_admin_db():
    try:
        db = AdminSessionLocal()
    except AdminDatabaseNotConfigured as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="admin database unavailable") from exc
    try:
        yield db
    finally:
        db.close()
