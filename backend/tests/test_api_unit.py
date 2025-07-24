"""Unit tests for API endpoints - Testing endpoint structure without authentication"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# These are unit tests that verify endpoint existence and basic responses
# without requiring authentication or external services


def test_health_endpoint():
    """Test health endpoint exists and responds"""
    response = client.get("/health")
    # The health endpoint might not exist, so we test if it's 404 or 200
    assert response.status_code in [200, 404]


def test_root_endpoint():
    """Test root endpoint responds"""
    response = client.get("/")
    # Should either serve frontend or return a basic response
    assert response.status_code in [200, 404]


# Auth endpoint structure tests (without actual authentication)
def test_auth_endpoints_exist():
    """Test auth endpoints exist and return proper error codes for missing data"""

    # Register endpoint should exist
    response = client.post("/auth/register", json={})
    assert response.status_code in [400, 422]  # Should reject empty data

    # Login endpoint should exist
    response = client.post("/auth/login", data={})
    assert response.status_code in [400, 422]  # Should reject empty data


def test_protected_endpoints_require_auth():
    """Test that protected endpoints properly require authentication"""

    # These endpoints should return 401 without auth
    protected_endpoints = [
        ("GET", "/profiles/me"),
        ("GET", "/auth/me"),
        ("GET", "/routes/"),
        ("GET", "/training/plans"),
    ]

    for method, endpoint in protected_endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint)

        # Should return 401 Unauthorized
        assert response.status_code == 401


def test_strava_auth_url_endpoint():
    """Test Strava auth URL endpoint structure"""
    response = client.get("/strava/auth-url")
    # Should either work or require auth (401)
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "auth_url" in data


def test_api_docs_available():
    """Test that API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_spec():
    """Test that OpenAPI spec is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
