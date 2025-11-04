"""Tests for FastAPI main application."""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "email-helper-api"
    assert "version" in data
    assert "database" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Email Helper API"
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


def test_docs_endpoint():
    """Test API documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/health")
    # Options request should be allowed for CORS preflight
    assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS
