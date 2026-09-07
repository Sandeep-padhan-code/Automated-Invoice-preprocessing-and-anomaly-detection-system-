import io
import json
import pytest
from fastapi.testclient import TestClient

from backend import app
import config


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_headers(client):
    response = client.get("/api/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "x-xss-protection" in response.headers


def test_invoices_list(client):
    response = client.get("/api/invoices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_statistics(client):
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "normal" in data
    assert "anomalous" in data


def test_analyze_valid_json(client):
    valid_invoice = {
        "invoice_number": "TEST-2024-001",
        "date": "2024-01-15",
        "vendor": "Acme Corp",
        "subtotal": 100.0,
        "tax": 10.0,
        "total": 110.0
    }
    file_bytes = json.dumps(valid_invoice).encode("utf-8")
    files = {"file": ("invoice.json", file_bytes, "application/json")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data.get("invoice_number") == "TEST-2024-001"
    assert data.get("final_decision") == "NORMAL"


def test_analyze_unsupported_extension(client):
    file_bytes = b"echo 'malicious script'"
    files = {"file": ("script.exe", file_bytes, "application/octet-stream")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data.get("analysis_status") == "UNABLE_TO_ANALYZE"
    assert "Unsupported file extension" in data.get("analysis_message", "")


def test_analyze_malformed_json(client):
    file_bytes = b"this is not valid json {"
    files = {"file": ("corrupt.json", file_bytes, "application/json")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data.get("analysis_status") == "UNABLE_TO_ANALYZE"


def test_analyze_file_too_large(client, monkeypatch):
    # Temporarily set MAX_UPLOAD_BYTES to 100 bytes for fast testing
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 100)
    oversized = b"a" * 500
    files = {"file": ("big.json", oversized, "application/json")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 413


def test_cors_headers(client):
    allowed_origin = config.ALLOWED_ORIGINS[0]
    response = client.options(
        "/api/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.headers.get("access-control-allow-origin") == allowed_origin
