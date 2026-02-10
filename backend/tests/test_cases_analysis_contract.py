from fastapi.routing import APIRoute

from app.main import app


def _paths():
    return [route.path for route in app.routes if isinstance(route, APIRoute)]


def test_case_analysis_route_exists():
    paths = _paths()
    assert "/api/v1/cases/{case_id}/analysis" in paths
