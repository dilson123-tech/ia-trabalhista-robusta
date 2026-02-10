import pytest
from fastapi import HTTPException

from app.core.security import require_role


def test_require_role_allows_admin():
    dep = require_role("admin")
    claims = {"sub": "admin", "role": "admin"}
    assert dep(claims) == claims


def test_require_role_forbids_non_admin():
    dep = require_role("admin")
    claims = {"sub": "user", "role": "advogado"}
    with pytest.raises(HTTPException) as exc:
        dep(claims)
    assert exc.value.status_code == 403


def test_require_role_without_args_allows_any_role():
    dep = require_role()
    claims = {"sub": "alguem", "role": "leitura"}
    # quando não passamos allowed, só devolve as claims
    assert dep(claims) == claims
