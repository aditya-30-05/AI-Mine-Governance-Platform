"""API contract tests using Starlette/FastAPI TestClient."""
import pytest
from starlette.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.main import app
from app.auth.security import create_access_token
from app.models import UserRole


@pytest.fixture
def client():
    # Use TestClient with lifespan context
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health_check(client):
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_protected_route_without_token(client):
    """Verify that unauthenticated calls to protected routes receive 401 Unauthorized."""
    response = client.get("/api/v1/mines")
    assert response.status_code == 401


def test_audit_ledger_summary_auth(client):
    """Verify audit ledger summary route exists and rejects unauthenticated requests."""
    response = client.get("/api/v1/audit/ledger-summary")
    assert response.status_code == 401


def test_login_validation_invalid_credentials(client):
    """Verify login validation rejects empty or invalid body."""
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code in [400, 422]
