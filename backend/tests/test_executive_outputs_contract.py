from fastapi.testclient import TestClient
import json
import uuid

import fpdf
from sqlalchemy import create_engine, text

from app.main import app
from app.core.settings import settings
from app.services import pdf_executive as pdf_executive_service

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_exec_{uuid.uuid4().hex[:8]}@example.com",
        "password": "dev",
        "role": "admin",
    }

    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": "test-seed-token"},
    )
    assert r_seed.status_code == 200
    assert r_seed.json()["ok"] is True

    r_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": seed_payload["username"],
            "password": seed_payload["password"],
        },
    )
    assert r_login.status_code == 200

    token = r_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_executive_outputs_contract_and_missing_case(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": f"EXEC-{uuid.uuid4()}",
        "title": "Caso executivo de contrato",
        "description": "Teste de summary, report e pdf.",
        "status": "draft",
    }

    create_resp = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert create_resp.status_code == 200
    case_id = create_resp.json()["id"]

    summary = client.get(f"/api/v1/cases/{case_id}/executive-summary", headers=headers)
    assert summary.status_code == 200
    summary_body = summary.json()
    assert summary_body["case"]["id"] == case_id
    assert summary_body["case"]["case_number"] == create_payload["case_number"]
    assert summary_body["case"]["title"] == create_payload["title"]
    assert "technical_analysis" in summary_body
    assert "strategic_analysis" in summary_body
    assert "viability" in summary_body
    assert "executive_decision" in summary_body

    report = client.get(f"/api/v1/cases/{case_id}/executive-report", headers=headers)
    assert report.status_code == 200
    report_body = report.json()
    assert report_body["case_id"] == case_id
    assert "executive_decision" in report_body
    assert "report_html" in report_body
    assert isinstance(report_body["report_html"], str)
    assert len(report_body["report_html"]) > 50

    pdf = client.get(f"/api/v1/cases/{case_id}/executive-pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert len(pdf.content) > 100

    missing_id = 999999

    missing_summary = client.get(f"/api/v1/cases/{missing_id}/executive-summary", headers=headers)
    assert missing_summary.status_code == 404

    missing_report = client.get(f"/api/v1/cases/{missing_id}/executive-report", headers=headers)
    assert missing_report.status_code == 404

    missing_pdf = client.get(f"/api/v1/cases/{missing_id}/executive-pdf", headers=headers)
    assert missing_pdf.status_code == 404

def test_executive_pdf_refreshes_stale_executive_data_before_generating(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": f"EXEC-STALE-{uuid.uuid4()}",
        "title": "Caso com executive_data legado",
        "description": "Teste de refresh de executive_data stale antes do PDF.",
        "status": "draft",
    }

    create_resp = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert create_resp.status_code == 200
    case_id = create_resp.json()["id"]

    analysis_resp = client.get(f"/api/v1/cases/{case_id}/analysis", headers=headers)
    assert analysis_resp.status_code == 200

    stale_payload = {
        "viability": {
            "score": 85,
            "probability": 0.85,
            "label": "Alta chance de êxito",
            "complexity": "Baixa",
            "estimated_time": "6-12 meses",
            "recommendation": "Recomendado entrar com a ação",
        },
        "decision": {
            "final_status": "FAVORÁVEL",
            "confidence_level": 85.0,
            "executive_recommendation": "Recomendado entrar com a ação",
            "estimated_complexity": "Baixa",
            "estimated_time": "6-12 meses",
        },
        "strategic": {
            "success_probability": 0.8,
            "complexity": "baixa",
            "financial_risk": "baixo",
            "recommended_strategy": "Reforçar provas documentais e preparar testemunhas.",
            "critical_points": [],
            "strong_points": ["Estrutura contratual existente"],
        },
    }

    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text("update case_analyses set executive_data = :payload where case_id = :case_id"),
            {"payload": json.dumps(stale_payload), "case_id": case_id},
        )

    captured = {}

    def _capture_pdf(case_data, executive_data):
        captured["case_data"] = case_data
        captured["executive_data"] = executive_data
        return b"%PDF-1.4 regression"

    monkeypatch.setattr("app.api.v1.routes.cases.generate_executive_pdf", _capture_pdf)

    pdf = client.get(f"/api/v1/cases/{case_id}/executive-pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF-1.4 regression")

    refreshed = captured["executive_data"]
    assert refreshed["decision"]["executive_summary"]
    assert refreshed["decision"]["probability_percent"] is not None
    assert refreshed["strategic"]["financial_risk"] in {"baixo", "medio", "alto"}


def test_pdf_fallback_uses_financial_risk_when_risk_level_is_missing(monkeypatch):
    captured = []
    real_fpdf = fpdf.FPDF

    class SpyFPDF(real_fpdf):
        def cell(self, *args, **kwargs):
            text_value = kwargs.get("txt") or kwargs.get("text")
            if text_value is None and len(args) >= 3:
                text_value = args[2]
            if text_value is not None:
                captured.append(str(text_value))
            return super().cell(*args, **kwargs)

        def multi_cell(self, *args, **kwargs):
            text_value = kwargs.get("txt") or kwargs.get("text")
            if text_value is None and len(args) >= 3:
                text_value = args[2]
            if text_value is not None:
                captured.append(str(text_value))
            return super().multi_cell(*args, **kwargs)

    monkeypatch.setattr(fpdf, "FPDF", SpyFPDF)

    pdf_bytes = pdf_executive_service._pdf_via_fpdf2(
        case_data={
            "case_number": "EXEC-FPDF-RISK",
            "title": "Caso fallback",
        },
        executive_data={
            "viability": {
                "probability": 0.34,
                "complexity": "Alta",
                "estimated_time": "24+ meses",
                "recommendation": "Reavaliar provas e estratégia antes de ajuizar",
            },
            "decision": {
                "executive_summary": "Resumo executivo de teste",
                "final_status": "ARRISCADA",
            },
            "strategic": {
                "financial_risk": "alto",
            },
        },
    )

    assert pdf_bytes.startswith(b"%PDF")
    assert any("Nivel de risco: Alto" in item for item in captured)

