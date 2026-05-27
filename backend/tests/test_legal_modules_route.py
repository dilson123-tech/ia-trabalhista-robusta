from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_legal_modules_returns_official_modules():
    response = client.get("/api/v1/legal-modules")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 7

    module_ids = {item["id"] for item in data}

    assert "trabalhista" in module_ids
    assert "civel" in module_ids
    assert "consumidor" in module_ids
    assert "familia" in module_ids
    assert "previdenciario" in module_ids
    assert "criminal" in module_ids
    assert "civil_ambiental" in module_ids


def test_get_legal_modules_payload_has_frontend_fields():
    response = client.get("/api/v1/legal-modules")

    assert response.status_code == 200

    first_module = response.json()[0]

    assert "id" in first_module
    assert "label" in first_module
    assert "canonical_legal_area" in first_module
    assert "status" in first_module
    assert "aliases" in first_module
    assert "action_keywords" in first_module
    assert "safety_notes" in first_module
