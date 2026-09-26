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
