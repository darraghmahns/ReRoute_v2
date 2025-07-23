import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# Helper function to get auth token
def get_auth_token():
    unique_email = f"test{int(time.time())}@example.com"
    # Register
    client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    # Login
    response = client.post(
        "/auth/login", data={"username": unique_email, "password": "testpassword123"}
    )
    return response.json()["access_token"]


# Auth endpoints
def test_register():
    # Use unique email to avoid conflicts
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


def test_login():
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_logout():
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]


def test_forgot_password():
    response = client.post("/auth/forgot-password", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert "Password reset email sent" in response.json()["message"]


def test_reset_password():
    response = client.post(
        "/auth/reset-password",
        json={"token": "test-token", "new_password": "newpassword123"},
    )
    assert response.status_code == 200
    assert "Password successfully reset" in response.json()["message"]


def test_verify():
    response = client.get("/auth/verify?token=test-token")
    assert response.status_code == 200
    assert "Email verified successfully" in response.json()["message"]


def test_me():
    # This will fail without authentication, but we can test the endpoint exists
    response = client.get("/auth/me")
    assert response.status_code == 401  # Unauthorized without token


# Profiles endpoints
def test_get_profile():
    # Test without authentication
    response = client.get("/profiles/me")
    assert response.status_code == 401  # Unauthorized without token


def test_update_profile():
    # Test without authentication
    response = client.put(
        "/profiles/me",
        json={
            "age": 30,
            "gender": "male",
            "weight_lbs": 165.0,
            "height_ft": 5,
            "height_in": 10,
        },
    )
    assert response.status_code == 401  # Unauthorized without token


def test_complete_profile():
    # Test without authentication
    response = client.post(
        "/profiles/complete",
        json={
            "step": 1,
            "data": {
                "age": 30,
                "gender": "male",
                "weight_lbs": 165.0,
                "height_ft": 5,
                "height_in": 10,
            },
        },
    )
    assert response.status_code == 401  # Unauthorized without token


def test_delete_profile():
    # Test without authentication
    response = client.delete("/profiles/me")
    assert response.status_code == 401  # Unauthorized without token


# Routes endpoints
def test_generate_route():
    response = client.post("/routes/generate")
    assert response.status_code == 200
    assert "generate route" in response.json()["message"]


def test_list_routes():
    response = client.get("/routes/")
    assert response.status_code == 200
    assert "list routes" in response.json()["message"]


def test_get_route():
    response = client.get("/routes/123")
    assert response.status_code == 200
    assert "get route" in response.json()["message"]


def test_delete_route():
    response = client.delete("/routes/123")
    assert response.status_code == 200
    assert "delete route" in response.json()["message"]


def test_download_gpx():
    response = client.get("/routes/123/gpx")
    assert response.status_code == 200
    assert "download gpx" in response.json()["message"]


def test_generate_loops():
    response = client.post("/routes/loops")
    assert response.status_code == 200
    assert "generate loops" in response.json()["message"]


# Training endpoints
def test_generate_plan():
    response = client.post("/training/plans")
    assert response.status_code == 200
    assert "generate plan" in response.json()["message"]


def test_list_plans():
    response = client.get("/training/plans")
    assert response.status_code == 200
    assert "list plans" in response.json()["message"]


def test_get_plan():
    response = client.get("/training/plans/123")
    assert response.status_code == 200
    assert "get plan" in response.json()["message"]


def test_update_plan():
    response = client.put("/training/plans/123")
    assert response.status_code == 200
    assert "update plan" in response.json()["message"]


def test_delete_plan():
    response = client.delete("/training/plans/123")
    assert response.status_code == 200
    assert "delete plan" in response.json()["message"]


def test_ai_update_plan():
    response = client.post("/training/plans/123/update")
    assert response.status_code == 200
    assert "ai update plan" in response.json()["message"]


# Strava endpoints
def test_get_auth_url():
    response = client.get("/strava/auth-url")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "strava.com" in data["auth_url"]


def test_handle_callback():
    # This endpoint requires authentication
    response = client.post("/strava/callback", json={"code": "test-code"})
    assert response.status_code == 401  # Unauthorized without token


def test_sync_activities():
    # This endpoint requires authentication
    response = client.post("/strava/sync")
    assert response.status_code == 401  # Unauthorized without token


def test_get_activities():
    # This endpoint requires authentication
    response = client.get("/strava/activities")
    assert response.status_code == 401  # Unauthorized without token


def test_fetch_zones():
    # This endpoint requires authentication
    response = client.post("/strava/zones")
    assert response.status_code == 401  # Unauthorized without token


def test_disconnect():
    # This endpoint requires authentication
    response = client.delete("/strava/disconnect")
    assert response.status_code == 401  # Unauthorized without token


# Chat endpoints
def test_send_message():
    # This endpoint requires authentication and proper request format
    response = client.post(
        "/chat/message", json={"messages": [{"role": "user", "content": "Hello"}]}
    )
    assert response.status_code == 401  # Unauthorized without token


def test_get_history():
    # This endpoint requires authentication
    response = client.get("/chat/history")
    assert response.status_code == 401  # Unauthorized without token


def test_clear_history():
    # This endpoint requires authentication
    response = client.delete("/chat/history")
    assert response.status_code == 401  # Unauthorized without token


# Analytics endpoints
def test_dashboard():
    response = client.get("/analytics/dashboard")
    assert response.status_code == 200
    assert "dashboard" in response.json()["message"]


def test_weekly():
    response = client.get("/analytics/weekly")
    assert response.status_code == 200
    assert "weekly" in response.json()["message"]


def test_metrics():
    response = client.get("/analytics/metrics")
    assert response.status_code == 200
    assert "metrics" in response.json()["message"]


def test_trends():
    response = client.get("/analytics/trends")
    assert response.status_code == 200
    assert "trends" in response.json()["message"]


# Subscription endpoints
def test_status():
    response = client.get("/subscription/status")
    assert response.status_code == 200
    assert "status" in response.json()["message"]


def test_checkout():
    response = client.post("/subscription/checkout")
    assert response.status_code == 200
    assert "checkout" in response.json()["message"]


def test_portal():
    response = client.post("/subscription/portal")
    assert response.status_code == 200
    assert "portal" in response.json()["message"]


def test_webhooks():
    response = client.post("/subscription/webhooks")
    assert response.status_code == 200
    assert "webhooks" in response.json()["message"]
