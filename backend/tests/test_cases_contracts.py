from fastapi.routing import APIRoute

from app.main import app


def _paths():
    # pega só rotas "normais" (sem docs, static, etc.)
    return [route.path for route in app.routes if isinstance(route, APIRoute)]


def test_cases_list_route_exists():
    paths = _paths()
    # contrato mínimo: rota de listagem de casos precisa existir
    assert "/api/v1/cases" in paths


def test_cases_detail_route_exists():
    paths = _paths()
    # contrato mínimo: rota de detalhe de caso precisa existir
    assert "/api/v1/cases/{case_id}" in paths
