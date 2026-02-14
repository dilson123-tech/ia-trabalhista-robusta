import os
import requests

BASE = os.getenv("TEST_BASE", "http://127.0.0.1:8099")

def _login(username: str, password: str) -> str:
    r = requests.post(f"{BASE}/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token")
    assert tok and len(tok) > 20
    return tok

def test_admin_only_admin_ok():
    tok = _login("admin@local", "dev")
    r = requests.get(f"{BASE}/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text

def test_admin_only_adv_forbidden():
    tok = _login("advogado@local", "dev")
    r = requests.get(f"{BASE}/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403, r.text
