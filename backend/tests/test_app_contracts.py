from fastapi.routing import APIRoute
from app.main import app


def _paths():
    # pega só rotas "normais" (sem docs, static, etc.)
    return [route.path for route in app.routes if isinstance(route, APIRoute)]


def test_health_route_exists():
    paths = _paths()
    # contrato mínimo: health precisa existir nesse caminho
    assert "/api/v1/health" in paths


def test_auth_seed_admin_route_exists():
    paths = _paths()
    # contrato mínimo: rota de seed-admin precisa existir
    assert "/api/v1/auth/seed-admin" in paths
