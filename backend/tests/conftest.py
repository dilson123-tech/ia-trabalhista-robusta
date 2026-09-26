import os

# ---------------------------------------------------------------------------
# Bootstrap hermético de configuração (BLOCO 1A / S2).
# Precisa rodar ANTES de qualquer import de `app`, pois `settings`, `engine`,
# `SessionLocal` e `LIMITS` são congelados no import.
# - IA_TRAB_TEST_MODE=1 faz app/core/settings.py NÃO carregar ROOT/.env.
# - Valores atribuídos diretamente (sem setdefault): o ambiente externo não
#   sobrepõe a baseline de teste.
# - Nenhum valor abaixo é segredo real; DATABASE_URL é sintético e não deve
#   ser usado para conectar.
# ---------------------------------------------------------------------------
_HERMETIC_TEST_ENV = {
    "IA_TRAB_TEST_MODE": "1",
    "AUTH_ENABLED": "true",
    "JWT_SECRET": "pytest-hermetic-jwt-secret-not-a-real-secret-0000",
    "DATABASE_URL": "postgresql+psycopg2://pytest:pytest@127.0.0.1:9/pytest_hermetic_not_connected",
    "LLM_ANALYSIS_ENABLED": "false",
}

# Variáveis lidas por Settings (ou no import/request) que devem cair nos
# defaults versionados, sem influência do ambiente externo.
_HERMETIC_UNSET_ENV = (
    "APP_NAME", "APP_ENV", "LOG_LEVEL", "LOG_HTTP", "AUDIT_EXCLUDE_PATHS",
    "AUTH_PROTECT_DOCS", "JWT_ALG", "JWT_EXPIRES_MIN",
    "ADMIN_SEED_TOKEN", "ALLOW_SEED_ADMIN", "ADMIN_API_KEY", "ADMIN_API_KEYS",
    "CORS_ALLOW_ORIGINS", "API_V1_PREFIX", "CASE_ATTACHMENT_STORAGE_DIR",
    "PLAN_BASIC_ACTIVE_CASES_LIMIT", "PLAN_BASIC_CASES_PER_MONTH",
    "PLAN_BASIC_CASE_RECORDS_LIMIT", "PLAN_BASIC_AI_ANALYSES_PER_MONTH",
    "PLAN_PRO_ACTIVE_CASES_LIMIT", "PLAN_PRO_CASES_PER_MONTH",
    "PLAN_PRO_CASE_RECORDS_LIMIT", "PLAN_PRO_AI_ANALYSES_PER_MONTH",
    "PLAN_OFFICE_ACTIVE_CASES_LIMIT", "PLAN_OFFICE_CASES_PER_MONTH",
    "PLAN_OFFICE_CASE_RECORDS_LIMIT", "PLAN_OFFICE_AI_ANALYSES_PER_MONTH",
    "LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_TIMEOUT_SECONDS", "LLM_BASE_URL",
    "PAYMENT_PROVIDER", "PAYMENT_CHECKOUT_BASE_URL",
    "ASAAS_API_KEY", "ASAAS_BASE_URL", "ASAAS_WEBHOOK_TOKEN",
)

# pydantic-settings casa nomes sem diferenciar maiúsculas/minúsculas.
_hermetic_managed = {name.upper() for name in (*_HERMETIC_TEST_ENV, *_HERMETIC_UNSET_ENV)}
for _name in list(os.environ):
    if _name.upper() in _hermetic_managed:
        del os.environ[_name]
os.environ.update(_HERMETIC_TEST_ENV)

import sys
from pathlib import Path

# BASE_DIR = raiz do backend (onde fica app/)
BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

import app.models  # noqa: F401  (garante Base.metadata com todos models)
import app.core.middleware as _app_middleware_module
import app.db.session as _app_db_session_module
import app.main as _app_main_module

# Banco isolado para testes
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_NO_OVERRIDE = object()


def _restore_get_db_override(previous):
    if previous is _NO_OVERRIDE:
        fastapi_app.dependency_overrides.pop(get_db, None)
    else:
        fastapi_app.dependency_overrides[get_db] = previous


@pytest.fixture(autouse=True)
def _hermetic_request_db(monkeypatch):
    """Todas as requests do teste usam o SQLite isolado; schema recriado por teste.

    - get_db: override em fastapi_app.dependency_overrides, resolvido no momento
      da request (cobre TestClient criado no nível de módulo).
    - SessionLocal importado por nome (middleware de auditoria e /ready):
      substituído no módulo consumidor; restaurado pelo monkeypatch.
    """
    Base.metadata.create_all(bind=engine)

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    previous = fastapi_app.dependency_overrides.get(get_db, _NO_OVERRIDE)
    fastapi_app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(_app_main_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(_app_middleware_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(_app_db_session_module, "SessionLocal", TestingSessionLocal)
    try:
        yield
    finally:
        _restore_get_db_override(previous)
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(_hermetic_request_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    previous = fastapi_app.dependency_overrides.get(get_db, _NO_OVERRIDE)
    fastapi_app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    try:
        with TestClient(fastapi_app) as c:
            yield c
    finally:
        _restore_get_db_override(previous)


# ---------------------------------------------------------------------------
# PostgreSQL 16 efêmero de TESTE (BLOCO 1A / S4) — opt-in, nunca autouse.
# SQLite acima continua sendo a camada padrão. Só testes que pedirem os
# fixtures pg_* abaixo tocam PostgreSQL; a URL vem exclusivamente de
# IA_TRAB_TEST_PG_OWNER_URL (e, no BLOCO 2, IA_TRAB_TEST_PG_APP_URL), validada
# por tests/pg_test_support.py. Sem fallback para settings.DATABASE_URL.
# ---------------------------------------------------------------------------
from sqlalchemy.orm import Session as _PgSession

from tests import pg_test_support as _pg


@pytest.fixture(scope="session")
def pg_test_owner_url():
    """URL owner/migration do servidor PG de teste (falha fechada se ausente/inválida)."""
    if not os.environ.get(_pg.OWNER_URL_ENV, "").strip():
        pytest.fail(
            f"{_pg.OWNER_URL_ENV} não definida: teste PostgreSQL exige servidor efêmero de teste "
            "(backend/tests/docker-compose.test-pg.yml)",
            pytrace=False,
        )
    try:
        return _pg.owner_url_from_env()
    except _pg.UnsafeTestDatabaseError as exc:
        pytest.fail(str(exc), pytrace=False)


@pytest.fixture(scope="session")
def pg_migrated_database_url(pg_test_owner_url):
    """Database exclusivo desta execução, com `alembic upgrade head`; removido ao final."""
    run_url = _pg.create_run_database(pg_test_owner_url)
    try:
        _pg.run_alembic_upgrade_head(run_url)
        yield run_url
    finally:
        _pg.drop_run_database(pg_test_owner_url, run_url)


@pytest.fixture(scope="session")
def pg_app_database_url(pg_migrated_database_url):
    """Ponto de extensão do BLOCO 2: URL da role de aplicação no database desta execução.

    Sem IA_TRAB_TEST_PG_APP_URL, usa a própria role owner (sem separação de roles ainda).
    """
    app_url = _pg.app_url_from_env()
    if app_url is None:
        return pg_migrated_database_url
    return _pg.assert_test_pg_url(
        app_url.set(database=pg_migrated_database_url.database),
        source=_pg.APP_URL_ENV,
    )


@pytest.fixture(scope="session")
def pg_engine(pg_app_database_url):
    engine_ = create_engine(pg_app_database_url, pool_pre_ping=True)
    try:
        yield engine_
    finally:
        engine_.dispose()


@pytest.fixture(scope="function")
def pg_session(pg_engine):
    """Sessão PG isolada por teste: transação externa sempre revertida (commits viram savepoints)."""
    connection = pg_engine.connect()
    transaction = connection.begin()
    session = _PgSession(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# Requests HTTP contra o PostgreSQL de TESTE (BLOCO 1A / S5) — opt-in.
# Estratégia: commit real no database exclusivo da execução + TRUNCATE antes e
# depois de cada teste. pg_session (rollback) não serve aqui: o TestClient
# atende as requests em outra thread/conexão, que não enxerga dados sem commit,
# e Session não é thread-safe para ser compartilhada.
# ---------------------------------------------------------------------------
from sqlalchemy import inspect as _sa_inspect
from sqlalchemy import text as _sa_text
from sqlalchemy.pool import NullPool as _NullPool
import weakref as _weakref


def _truncate_pg_test_tables(owner_run_url):
    """Esvazia todas as tabelas do database de execução (exceto alembic_version)."""
    _pg.assert_test_pg_url(owner_run_url, source="pg_request_db")
    _pg._assert_run_database(owner_run_url.database)
    cleanup_engine = create_engine(owner_run_url, poolclass=_NullPool)
    try:
        with cleanup_engine.begin() as conn:
            tables = [
                name
                for name in _sa_inspect(conn).get_table_names(schema="public")
                if name != "alembic_version"
            ]
            if tables:
                quoted = ", ".join(f'public."{name}"' for name in tables)
                conn.execute(_sa_text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    finally:
        cleanup_engine.dispose()


@pytest.fixture(scope="function")
def pg_request_db(_hermetic_request_db, monkeypatch, pg_migrated_database_url, pg_app_database_url):
    """Aponta get_db, middleware de auditoria e /ready para o PG de teste; devolve a factory de sessão.

    - Roda depois da autouse SQLite e sobrepõe seu override/monkeypatch; restaura ao final.
    - Setup direto usa a factory devolvida e faz commit real (visível às requests).
    - Engine própria por teste: conexões com app.tenant_id (set_config de sessão)
      são descartadas no teardown e não vazam para o teste seguinte. Não há reset
      por checkin, para não mascarar vazamento de contexto dentro do próprio teste.
    """
    _truncate_pg_test_tables(pg_migrated_database_url)

    request_engine = create_engine(pg_app_database_url, pool_pre_ping=True)
    _pg_sessionmaker = sessionmaker(
        autocommit=False, autoflush=False, bind=request_engine, expire_on_commit=False
    )
    opened_sessions = _weakref.WeakSet()

    def PgSessionLocal():
        # Uma Session nova por chamada (por request/thread); rastreada para o teardown.
        session = _pg_sessionmaker()
        opened_sessions.add(session)
        return session

    def _override_get_db():
        db = PgSessionLocal()
        try:
            yield db
        finally:
            db.close()

    previous = fastapi_app.dependency_overrides.get(get_db, _NO_OVERRIDE)
    fastapi_app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(_app_main_module, "SessionLocal", PgSessionLocal)
    monkeypatch.setattr(_app_middleware_module, "SessionLocal", PgSessionLocal)
    monkeypatch.setattr(_app_db_session_module, "SessionLocal", PgSessionLocal)
    try:
        yield PgSessionLocal
    finally:
        _restore_get_db_override(previous)
        # Sessão deixada aberta por falha no meio do teste seguraria locks e travaria o TRUNCATE.
        for session in list(opened_sessions):
            session.close()
        request_engine.dispose()
        _truncate_pg_test_tables(pg_migrated_database_url)
