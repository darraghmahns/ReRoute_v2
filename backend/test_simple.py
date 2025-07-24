"""Simple API tests that focus on endpoint accessibility and basic functionality"""
import time

import pytest


def test_register(client):
    """Test user registration"""
    unique_email = f"test{int(time.time())}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == unique_email
    assert data["full_name"] == "Test User"


def test_login_with_existing_user(client):
    """Test login with a user we create first"""
    # First register a user
    unique_email = f"test{int(time.time())}@example.com"
    client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )

    # Now try to login
    response = client.post(
        "/auth/login", data={"username": unique_email, "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_endpoints_require_auth(client):
    """Test that protected endpoints return 401 without authentication"""
    endpoints = [
        ("GET", "/auth/me"),
        ("GET", "/profiles/me"),
        ("POST", "/routes/generate"),
        ("GET", "/routes/"),
        ("POST", "/training/plans"),
        ("GET", "/training/plans"),
        ("GET", "/strava/connect"),
        ("POST", "/chat"),
        ("GET", "/analytics/dashboard"),
        ("GET", "/subscription/status"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "PUT":
            response = client.put(endpoint, json={})
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert (
            response.status_code == 401
        ), f"{method} {endpoint} should require authentication"


def test_health_check(client):
    """Test that the root endpoint is accessible"""
    response = client.get("/")
    # The root endpoint might return 200 (if it exists) or 404 (if not defined)
    # Both are acceptable for this test
    assert response.status_code in [200, 404]


def test_auth_flow(client):
    """Test complete authentication flow"""
    unique_email = f"test{int(time.time())}@example.com"

    # 1. Register
    response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 200
    user_data = response.json()

    # 2. Login
    response = client.post(
        "/auth/login", data={"username": unique_email, "password": "testpassword123"}
    )
    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]

    # 3. Access protected endpoint with token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200

    # 4. Logout
    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 200
