"""Suporte a PostgreSQL 16 efêmero EXCLUSIVO de teste (BLOCO 1A / S4).

Separação:
  A) servidor PG 16 .......... backend/tests/docker-compose.test-pg.yml (fora do pytest)
  B) banco de teste .......... create_run_database / drop_run_database (um database novo por execução)
  C) migrations .............. run_alembic_upgrade_head (subprocesso, somente após as guardas)
  D) fixtures pytest ......... backend/tests/conftest.py (pg_*)

Fonte da URL: SOMENTE variáveis explícitas de teste. Não há fallback para
settings.DATABASE_URL, DATABASE_URL do ambiente, .env ou qualquer default.

  IA_TRAB_TEST_PG_OWNER_URL  (obrigatória) role owner/migration; database base de teste

Roles de aplicação (BLOCO 2 / RLS): create_test_roles cria, somente no PG
efêmero de teste, uma role runtime e uma role admin sintéticas (LOGIN,
NOSUPERUSER, NOBYPASSRLS, NOCREATEDB, NOCREATEROLE, NOREPLICATION, não owner);
a admin é membro da role NOLOGIN ia_rls_admin. Migrations rodam como owner;
as requests e sessões de teste NUNCA usam a URL owner (sem fallback).
drop_test_roles remove as roles sintéticas antes do DROP DATABASE.

Toda URL passa por assert_test_pg_url antes de qualquer conexão; qualquer
dúvida => erro (falha fechada).
"""

from __future__ import annotations

import os
import re
import secrets
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

# Marcadores obrigatórios de TESTE.
TEST_DATABASE_PREFIX = "ia_trab_test"
TEST_ROLE_PREFIX = "ia_trab_test"
RUN_DATABASE_RE = re.compile(r"^ia_trab_test_run_[0-9a-f]{12}$")
# Roles sintéticas criadas por create_test_roles (runtime/admin).
TEST_APP_ROLE_RE = re.compile(r"^ia_trab_test_(rt|adm)_[0-9a-f]{12}$")
# Role NOLOGIN cuja membership concede acesso administrativo nas policies RLS.
RLS_ADMIN_ROLE = "ia_rls_admin"

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



def _assert_test_app_role(name: str) -> None:
    if not TEST_APP_ROLE_RE.fullmatch(name):
        raise UnsafeTestDatabaseError(f"role de teste {name!r} fora do padrão {TEST_APP_ROLE_RE.pattern}")


_ROLE_ATTRS = "LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION"


def create_test_roles(owner_run_url: URL) -> tuple[URL, URL, tuple[str, str]]:
    """(B') Cria as roles sintéticas runtime/admin SOMENTE no PG efêmero de teste.

    Retorna (runtime_url, admin_url, (runtime_role, admin_role)). Ambas as roles:
    LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION, sem
    ownership de tabelas; a admin é membro de ia_rls_admin (NOLOGIN, criada se
    não existir e nunca removida). Senhas aleatórias por execução; nenhuma
    mensagem de erro expõe senha (hide_parameters + exceção sanitizada).
    """
    owner_run_url = assert_test_pg_url(owner_run_url, source="create_test_roles")
    _assert_run_database(owner_run_url.database)

    suffix = uuid.uuid4().hex[:12]
    runtime_role = f"{TEST_ROLE_PREFIX}_rt_{suffix}"
    admin_role = f"{TEST_ROLE_PREFIX}_adm_{suffix}"
    for role in (runtime_role, admin_role):
        _assert_test_app_role(role)
    passwords = {runtime_role: secrets.token_hex(24), admin_role: secrets.token_hex(24)}
    database = owner_run_url.database

    engine = create_engine(owner_run_url, isolation_level="AUTOCOMMIT", hide_parameters=True)
    try:
        with engine.connect() as conn:
            for role, password in passwords.items():
                # psycopg2 interpola o parâmetro no cliente; hide_parameters oculta-o em erros.
                conn.execute(text(f'CREATE ROLE "{role}" {_ROLE_ATTRS} PASSWORD :pw'), {"pw": password})

            exists = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :r"), {"r": RLS_ADMIN_ROLE}
            ).first()
            if exists is None:
                conn.execute(text(f'CREATE ROLE "{RLS_ADMIN_ROLE}" NOLOGIN NOSUPERUSER NOBYPASSRLS'))
            conn.execute(text(f'GRANT "{RLS_ADMIN_ROLE}" TO "{admin_role}"'))

            for role in (runtime_role, admin_role):
                conn.execute(text(f'GRANT CONNECT ON DATABASE "{database}" TO "{role}"'))
                conn.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role}"'))

            # Runtime: aplicação normal, sujeita ao tenant RLS.
            conn.execute(
                text(
                    f'GRANT SELECT, INSERT, UPDATE, DELETE '
                    f'ON ALL TABLES IN SCHEMA public TO "{runtime_role}"'
                )
            )
            conn.execute(
                text(
                    f'GRANT USAGE, SELECT ON ALL SEQUENCES '
                    f'IN SCHEMA public TO "{runtime_role}"'
                )
            )

            # Admin: descoberta/leitura cross-tenant apenas.
            # Mutações devem voltar para a role runtime após conhecer o tenant.
            conn.execute(
                text(f'GRANT SELECT ON ALL TABLES IN SCHEMA public TO "{admin_role}"')
            )

            _verify_test_roles(conn, runtime_role, admin_role)
    except UnsafeTestDatabaseError:
        raise
    except Exception as exc:
        # Não propagar a mensagem original (pode conter o comando com a senha).
        raise RuntimeError(
            f"falha ao criar roles de teste no database {database!r} ({type(exc).__name__})"
        ) from None
    finally:
        engine.dispose()

    runtime_url = assert_test_pg_url(
        owner_run_url.set(username=runtime_role, password=passwords[runtime_role]), source="create_test_roles"
    )
    admin_url = assert_test_pg_url(
        owner_run_url.set(username=admin_role, password=passwords[admin_role]), source="create_test_roles"
    )
    return runtime_url, admin_url, (runtime_role, admin_role)


def _verify_test_roles(conn, runtime_role: str, admin_role: str) -> None:
    rows = conn.execute(
        text(
            "SELECT rolname, rolcanlogin, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolreplication "
            "FROM pg_catalog.pg_roles WHERE rolname IN (:rt, :adm, :rls)"
        ),
        {"rt": runtime_role, "adm": admin_role, "rls": RLS_ADMIN_ROLE},
    ).all()
    by_name = {row[0]: row for row in rows}
    for role in (runtime_role, admin_role):
        row = by_name.get(role)
        if row is None or tuple(row[1:]) != (True, False, False, False, False, False):
            raise UnsafeTestDatabaseError(f"role de teste {role!r} com atributos inesperados")
    rls = by_name.get(RLS_ADMIN_ROLE)
    if rls is None or rls[1] or rls[2] or rls[3]:
        raise UnsafeTestDatabaseError(f"role {RLS_ADMIN_ROLE!r} deve ser NOLOGIN NOSUPERUSER NOBYPASSRLS")

    owned = conn.execute(
        text("SELECT count(*) FROM pg_catalog.pg_tables WHERE tableowner IN (:rt, :adm)"),
        {"rt": runtime_role, "adm": admin_role},
    ).scalar_one()
    if owned:
        raise UnsafeTestDatabaseError("roles de teste runtime/admin não podem ser owner de tabelas")

    membership = conn.execute(
        text(
            "SELECT pg_catalog.pg_has_role(:rt, :rls, 'MEMBER'), pg_catalog.pg_has_role(:adm, :rls, 'MEMBER')"
        ),
        {"rt": runtime_role, "adm": admin_role, "rls": RLS_ADMIN_ROLE},
    ).one()
    if membership != (False, True):
        raise UnsafeTestDatabaseError(f"membership em {RLS_ADMIN_ROLE!r} inesperada para roles de teste")


def drop_test_roles(owner_run_url: URL, role_names: tuple[str, ...]) -> None:
    """(B') Remove as roles sintéticas; deve rodar ANTES de drop_run_database.

    DROP OWNED BY no database de execução revoga os grants (incluindo CONNECT);
    roles são globais do cluster, por isso são removidas explicitamente.
    ia_rls_admin nunca é removida.
    """
    owner_run_url = assert_test_pg_url(owner_run_url, source="drop_test_roles")
    _assert_run_database(owner_run_url.database)
    for role in role_names:
        _assert_test_app_role(role)

    engine = create_engine(owner_run_url, isolation_level="AUTOCOMMIT", hide_parameters=True)
    try:
        with engine.connect() as conn:
            for role in role_names:
                conn.execute(text(f'DROP OWNED BY "{role}"'))
                conn.execute(text(f'DROP ROLE IF EXISTS "{role}"'))
    finally:
        engine.dispose()

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
