import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def _test_env_defaults():
    os.environ["ADMIN_SEED_TOKEN"] = "TEST_SEED_TOKEN_123"
    os.environ.setdefault("JWT_SECRET", "x" * 64)

    # limpar cache do settings (import tardio para evitar ciclo)
    from app.core.settings import get_settings
    get_settings.cache_clear()

    yield
