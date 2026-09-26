"""Suporte a PostgreSQL 16 efêmero EXCLUSIVO de teste (BLOCO 1A / S4).

Separação:
  A) servidor PG 16 .......... backend/tests/docker-compose.test-pg.yml (fora do pytest)
  B) banco de teste .......... create_run_database / drop_run_database (um database novo por execução)
  C) migrations .............. run_alembic_upgrade_head (subprocesso, somente após as guardas)
  D) fixtures pytest ......... backend/tests/conftest.py (pg_*)

Fonte da URL: SOMENTE variáveis explícitas de teste. Não há fallback para
settings.DATABASE_URL, DATABASE_URL do ambiente, .env ou qualquer default.

  IA_TRAB_TEST_PG_OWNER_URL  (obrigatória) role owner/migration; database base de teste
  IA_TRAB_TEST_PG_APP_URL    (opcional, BLOCO 2) role de aplicação; se ausente, os
                             fixtures usam a URL owner

Toda URL passa por assert_test_pg_url antes de qualquer conexão; qualquer
dúvida => erro (falha fechada).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import NoReturn

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"

OWNER_URL_ENV = "IA_TRAB_TEST_PG_OWNER_URL"
APP_URL_ENV = "IA_TRAB_TEST_PG_APP_URL"

# Marcadores obrigatórios de TESTE.
TEST_DATABASE_PREFIX = "ia_trab_test"
TEST_ROLE_PREFIX = "ia_trab_test"
RUN_DATABASE_RE = re.compile(r"^ia_trab_test_run_[0-9a-f]{12}$")

_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
# Porta do PG de desenvolvimento em docker-compose.yml da raiz.
_FORBIDDEN_PORTS = frozenset({55432})
# Nomes de database de desenvolvimento/CI conhecidos.
_FORBIDDEN_DATABASES = frozenset({"ia_trabalhista", "ia_trab", "postgres", "template0", "template1"})


class UnsafeTestDatabaseError(RuntimeError):
    """Destino de PostgreSQL não identificável com segurança como TESTE."""


def _fail(source: str, reason: str) -> NoReturn:
    raise UnsafeTestDatabaseError(f"[{source}] alvo PostgreSQL recusado: {reason}")


def assert_test_pg_url(raw_url: str | URL | None, *, source: str) -> URL:
    """Valida que a URL aponta inequivocamente para PG de TESTE; senão, levanta."""
    if os.environ.get("IA_TRAB_TEST_MODE") != "1":
        _fail(source, "IA_TRAB_TEST_MODE=1 ausente (bootstrap hermético não ativo)")
    if raw_url is None or (isinstance(raw_url, str) and not raw_url.strip()):
        _fail(source, "URL ausente/vazia")

    try:
        url = raw_url if isinstance(raw_url, URL) else make_url(raw_url.strip())
    except Exception:
        _fail(source, "URL inválida")

    if url.get_backend_name() != "postgresql":
        _fail(source, f"backend {url.get_backend_name()!r} não é postgresql")
    if url.host not in _ALLOWED_HOSTS:
        _fail(source, f"host {url.host!r} não é loopback local")
    if url.port is None:
        _fail(source, "porta explícita obrigatória")
    if url.port in _FORBIDDEN_PORTS:
        _fail(source, f"porta {url.port} é a do PostgreSQL de desenvolvimento")
    if not url.database or url.database in _FORBIDDEN_DATABASES:
        _fail(source, f"database {url.database!r} proibido")
    if not url.database.startswith(TEST_DATABASE_PREFIX):
        _fail(source, f"database {url.database!r} sem prefixo {TEST_DATABASE_PREFIX!r}")
    if not url.username or not url.username.startswith(TEST_ROLE_PREFIX):
        _fail(source, f"role {url.username!r} sem prefixo {TEST_ROLE_PREFIX!r}")

    # Nunca coincidir com a URL da aplicação (settings ou ambiente).
    rendered = url.render_as_string(hide_password=False)
    app_urls = [os.environ.get(name) for name in os.environ if name.upper() == "DATABASE_URL"]
    try:
        from app.core.settings import settings

        app_urls.append(settings.DATABASE_URL)
    except Exception:
        pass
    for app_url in app_urls:
        if not app_url:
            continue
        try:
            same = make_url(app_url).render_as_string(hide_password=False) == rendered
        except Exception:
            same = app_url.strip() == rendered
        if same:
            _fail(source, "URL coincide com DATABASE_URL da aplicação")

    return url


def owner_url_from_env() -> URL:
    return assert_test_pg_url(os.environ.get(OWNER_URL_ENV), source=OWNER_URL_ENV)


def app_url_from_env() -> URL | None:
    """Ponto de extensão do BLOCO 2 (role de aplicação separada). None se não definida."""
    raw = os.environ.get(APP_URL_ENV)
    if raw is None or not raw.strip():
        return None
    return assert_test_pg_url(raw, source=APP_URL_ENV)


def _assert_run_database(name: str) -> None:
    if not RUN_DATABASE_RE.fullmatch(name):
        raise UnsafeTestDatabaseError(f"database de execução {name!r} fora do padrão {RUN_DATABASE_RE.pattern}")


def create_run_database(owner_url: URL) -> URL:
    """(B) Cria um database novo e exclusivo desta execução; retorna a URL owner apontando para ele."""
    owner_url = assert_test_pg_url(owner_url, source="create_run_database")
    name = f"{TEST_DATABASE_PREFIX}_run_{uuid.uuid4().hex[:12]}"
    _assert_run_database(name)

    admin_engine = create_engine(owner_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        admin_engine.dispose()

    return assert_test_pg_url(owner_url.set(database=name), source="create_run_database")


def drop_run_database(owner_url: URL, run_url: URL) -> None:
    """(B) Remove somente o database criado por create_run_database."""
    owner_url = assert_test_pg_url(owner_url, source="drop_run_database")
    run_url = assert_test_pg_url(run_url, source="drop_run_database")
    _assert_run_database(run_url.database)
    if run_url.database == owner_url.database:
        raise UnsafeTestDatabaseError("recusado: database de execução igual ao database base")

    admin_engine = create_engine(owner_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{run_url.database}" WITH (FORCE)'))
    finally:
        admin_engine.dispose()


def run_alembic_upgrade_head(run_url: URL) -> None:
    """(C) `alembic upgrade head` somente contra o database de execução de teste.

    alembic/env.py usa settings.DATABASE_URL; por isso roda em subprocesso com
    IA_TRAB_TEST_MODE=1 (sem .env) e DATABASE_URL = URL de teste já validada.
    O processo do pytest não tem settings nem logging alterados.
    """
    run_url = assert_test_pg_url(run_url, source="run_alembic_upgrade_head")
    _assert_run_database(run_url.database)

    env = {k: v for k, v in os.environ.items() if k.upper() != "DATABASE_URL"}
    env["IA_TRAB_TEST_MODE"] = "1"
    env["APP_ENV"] = "test"
    env["JWT_SECRET"] = "pytest-alembic-hermetic-jwt-secret-not-a-real-secret-0000"
    env["AUTH_ENABLED"] = "true"
    env["LLM_ANALYSIS_ENABLED"] = "false"
    env["DATABASE_URL"] = run_url.render_as_string(hide_password=False)

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head falhou no database de teste {run_url.database!r} "
            f"(exit {result.returncode}):\n{result.stderr[-4000:]}"
        )
