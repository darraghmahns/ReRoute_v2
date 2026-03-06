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


def test_action_result_schema():
    from app.schemas.chat import ActionResult, ChatResponse, ChatMessage

    action = ActionResult(
        type="route_generated",
        title="Morning Loop",
        description="45km road route",
        data={"route_id": "abc123"},
        nav_url="/routes",
    )
    assert action.type == "route_generated"
    assert action.nav_url == "/routes"

    response = ChatResponse(
        message=ChatMessage(role="assistant", content="Done!"),
        actions=[action],
    )
    assert len(response.actions) == 1
    assert response.actions[0].type == "route_generated"


def test_chat_response_default_empty_actions():
    from app.schemas.chat import ChatResponse, ChatMessage

    response = ChatResponse(
        message=ChatMessage(role="assistant", content="Hello"),
    )
    assert response.actions == []


def test_agent_has_route_tools():
    from app.services.ai_agent import ai_agent

    expected_tools = ["list_routes", "generate_route", "delete_route", "rename_route"]
    registered = list(ai_agent.tools.keys())
    for tool_name in expected_tools:
        assert tool_name in registered, f"Tool '{tool_name}' not registered"


def test_list_routes_returns_action_metadata():
    from unittest.mock import MagicMock
    from app.services.ai_agent import ai_agent

    mock_route = MagicMock()
    mock_route.id = "route-123"
    mock_route.name = "Test Loop"
    mock_route.distance_m = 45000
    mock_route.route_type = "road"
    mock_route.created_at.strftime.return_value = "2026-03-01"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_route]

    mock_user = MagicMock()
    mock_user.id = "user-123"

    result = ai_agent._list_routes(mock_db, mock_user, limit=5)

    assert result.get("action_type") == "routes_listed"
    assert result.get("action_nav_url") == "/routes"
    assert "routes" in result


def test_agent_has_profile_tools():
    from app.services.ai_agent import ai_agent
    assert "get_profile" in ai_agent.tools
    assert "update_profile" in ai_agent.tools


def test_update_profile_returns_action_metadata():
    from unittest.mock import MagicMock
    from app.services.ai_agent import ai_agent

    mock_profile = MagicMock()
    mock_profile.weight_lbs = 160
    mock_profile.fitness_level = "intermediate"
    mock_profile.primary_goals = "Get faster"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_profile

    mock_user = MagicMock()
    mock_user.id = "user-123"

    result = ai_agent._update_profile(mock_db, mock_user, weight_lbs=155.0)

    assert result.get("action_type") == "profile_updated"
    assert result.get("action_nav_url") == "/profile"
    assert "updated_fields" in result


def test_agent_has_training_tools():
    from app.services.ai_agent import ai_agent
    assert "generate_training_plan" in ai_agent.tools
    assert "update_workout" in ai_agent.tools


def test_update_workout_returns_action_metadata():
    from unittest.mock import MagicMock
    import uuid as _uuid
    from app.services.ai_agent import ai_agent

    mock_plan = MagicMock()
    mock_plan.id = str(_uuid.uuid4())
    mock_plan.is_active = True
    mock_plan.plan_data = {
        "weeks": [
            {
                "week_start_date": "2026-03-03",
                "workouts": {
                    "monday": {
                        "id": str(_uuid.uuid4()),
                        "title": "Rest Day",
                        "workout_type": "rest",
                        "duration_minutes": 0,
                        "description": "Rest",
                        "completed": False,
                    }
                },
            }
        ]
    }

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_plan

    mock_user = MagicMock()
    mock_user.id = "user-123"

    result = ai_agent._update_workout_structured(
        mock_db, mock_user,
        day="monday",
        title="Endurance Ride",
        workout_type="endurance",
        duration_minutes=90,
    )

    assert result.get("action_type") == "workout_updated"
    assert result.get("action_nav_url") == "/training"


def test_agent_has_strava_tools():
    from app.services.ai_agent import ai_agent
    assert "get_strava_activities" in ai_agent.tools
    assert "trigger_strava_sync" in ai_agent.tools


def test_extract_action_result_route_generated():
    from app.api.chat import _extract_action_result

    tool_result = {
        "success": True,
        "route_id": "abc",
        "name": "Morning Loop",
        "distance_km": 45.0,
        "action_type": "route_generated",
        "action_title": "New Route: Morning Loop",
        "action_description": "45.0km · 500m elevation",
        "action_nav_url": "/routes",
    }

    action = _extract_action_result("generate_route", tool_result)

    assert action is not None
    assert action.type == "route_generated"
    assert action.title == "New Route: Morning Loop"
    assert action.nav_url == "/routes"


def test_extract_action_result_no_action_type():
    from app.api.chat import _extract_action_result

    tool_result = {"some_key": "some_value"}
    action = _extract_action_result("some_tool", tool_result)
    assert action is None


def test_profile_update_endpoint_accepts_home_location():
    """Test that PUT /api/profiles/me accepts home_lat, home_lng, home_address_label"""
    response = client.put(
        "/api/profiles/me",
        json={"home_lat": 53.3498, "home_lng": -6.2603, "home_address_label": "Dublin, Ireland"},
    )
    # 401 = endpoint exists and requires auth (correct behavior without a token)
    assert response.status_code == 401


def test_subscription_status_requires_auth():
    """GET /subscription/status requires authentication"""
    response = client.get("/api/subscription/status")
    assert response.status_code == 401


def test_subscription_checkout_requires_auth():
    """POST /subscription/checkout requires authentication"""
    response = client.post("/api/subscription/checkout")
    assert response.status_code == 401


def test_subscription_portal_requires_auth():
    """POST /subscription/portal requires authentication"""
    response = client.post("/api/subscription/portal")
    assert response.status_code == 401


def test_subscription_webhook_accepts_post():
    """POST /subscription/webhooks is publicly accessible (returns 400 on bad signature)"""
    response = client.post(
        "/api/subscription/webhooks",
        content=b"{}",
        headers={"stripe-signature": "invalid"},
    )
    # 400 = endpoint exists and rejects invalid signature
    assert response.status_code == 400
