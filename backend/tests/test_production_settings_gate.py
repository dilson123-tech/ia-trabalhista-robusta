"""Gate de settings production-like (Missão 004 / F3).

Valida `validate_production_settings()` diretamente sobre o singleton
`settings`, alterando atributos via monkeypatch (restaurados ao fim de cada
teste). Nenhum .env, segredo real ou banco é lido/usado.
"""

import pytest

import app.core.settings as settings_module
from app.core.settings import validate_production_settings

PRODUCTION_LIKE_ENVS = ["prod", "production", "staging", " PROD ", "Staging"]
NON_PRODUCTION_ENVS = ["dev", "test", "ci", "local"]

_SAFE_DATABASE_URL = "postgresql+psycopg2://gate:gate@db.invalid:5432/gate_not_connected"


@pytest.fixture
def prod_like_valid(monkeypatch):
    """Configuração production-like que satisfaz todas as validações atuais."""
    s = settings_module.settings
    monkeypatch.setattr(s, "APP_ENV", "production")
    monkeypatch.setattr(s, "AUTH_ENABLED", True)
    monkeypatch.setattr(s, "AUTH_PROTECT_DOCS", True)
    monkeypatch.setattr(s, "DATABASE_URL", _SAFE_DATABASE_URL)
    monkeypatch.setattr(s, "ALLOW_SEED_ADMIN", False)
    return s


@pytest.mark.parametrize("app_env", PRODUCTION_LIKE_ENVS)
def test_production_like_rejects_auth_disabled(prod_like_valid, monkeypatch, app_env):
    monkeypatch.setattr(prod_like_valid, "APP_ENV", app_env)
    monkeypatch.setattr(prod_like_valid, "AUTH_ENABLED", False)

    with pytest.raises(RuntimeError, match="AUTH_ENABLED"):
        validate_production_settings()


@pytest.mark.parametrize("app_env", PRODUCTION_LIKE_ENVS)
def test_production_like_accepts_auth_enabled(prod_like_valid, monkeypatch, app_env):
    monkeypatch.setattr(prod_like_valid, "APP_ENV", app_env)

    validate_production_settings()


@pytest.mark.parametrize("app_env", NON_PRODUCTION_ENVS)
def test_non_production_allows_auth_disabled(monkeypatch, app_env):
    s = settings_module.settings
    monkeypatch.setattr(s, "APP_ENV", app_env)
    monkeypatch.setattr(s, "AUTH_ENABLED", False)

    validate_production_settings()


def test_production_like_still_rejects_default_database_url(prod_like_valid, monkeypatch):
    monkeypatch.setattr(
        prod_like_valid,
        "DATABASE_URL",
        "postgresql+psycopg2://ia_app:ia_app_pass@127.0.0.1:55432/ia_trabalhista",
    )

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_production_settings()


def test_production_like_still_rejects_seed_admin_without_real_token(prod_like_valid, monkeypatch):
    monkeypatch.setattr(prod_like_valid, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(prod_like_valid, "ADMIN_SEED_TOKEN", "CHANGE_ME_SEED_TOKEN")

    with pytest.raises(RuntimeError, match="ADMIN_SEED_TOKEN"):
        validate_production_settings()


def test_production_like_still_rejects_unprotected_docs(prod_like_valid, monkeypatch):
    monkeypatch.setattr(prod_like_valid, "AUTH_PROTECT_DOCS", False)

    with pytest.raises(RuntimeError, match="AUTH_PROTECT_DOCS"):
        validate_production_settings()
