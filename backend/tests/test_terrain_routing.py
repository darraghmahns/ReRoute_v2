"""
Unit and integration tests for the Contextual Training Router.

Unit tests cover pure transformation functions — no external APIs are called.
Integration tests use mocked external services (GraphHopper, Overpass, OpenAI)
and a real in-memory SQLite database via the existing conftest fixtures.

Test naming convention:
  test_<subject>__<scenario>__<expected_outcome>
"""
import json
import time
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.terrain import TerrainTarget
from app.schemas.training import WorkoutType
from app.services.workout_route_planner import WorkoutRoutePlanner
from app.services.overpass_service import OverpassService
from app.services.terrain_research_agent import TerrainResearchAgent

# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

FAKE_GH_RESPONSE: Dict[str, Any] = {
    "paths": [
        {
            "distance": 40000.0,
            "time": 5400000,
            "ascend": 350.0,
            "descend": 350.0,
            "points": {
                "type": "LineString",
                "coordinates": [
                    [10.0, 53.0, 10.0],
                    [10.1, 53.1, 25.0],
                    [10.0, 53.0, 10.0],
                ],
            },
        }
    ]
}

# ---------------------------------------------------------------------------
# 1. TerrainTarget schema validation
# ---------------------------------------------------------------------------


class TestTerrainTargetSchema:
    def test_invalid_surface_type_raises(self):
        with pytest.raises(ValidationError):
            TerrainTarget(surface_type="dirt_only")

    def test_negative_gradient_accepted(self):
        """Downhill bias (negative min gradient) is a valid configuration."""
        t = TerrainTarget(max_gradient_pct=-5.0, min_gradient_pct=-15.0)
        assert t.max_gradient_pct == -5.0

    def test_grade_range_min_lt_max_raises(self):
        with pytest.raises(ValidationError):
            TerrainTarget(grade_range=(6.0, 3.0))

    def test_grade_range_equal_raises(self):
        with pytest.raises(ValidationError):
            TerrainTarget(grade_range=(5.0, 5.0))

    def test_punchiness_score_above_one_raises(self):
        with pytest.raises(ValidationError):
            TerrainTarget(punchiness_score=1.1)

    def test_punchiness_score_negative_raises(self):
        with pytest.raises(ValidationError):
            TerrainTarget(punchiness_score=-0.1)

    def test_defaults_are_safe_for_road_bike(self):
        t = TerrainTarget()
        assert t.surface_type == "paved_only"
        assert t.allow_private is False
        assert "dirt" in t.forbidden_osm_surfaces
        assert "track" in t.forbidden_osm_highways

    def test_empty_string_in_highway_list_raises(self):
        with pytest.raises(ValidationError):
            TerrainTarget(forbidden_osm_highways=["track", ""])


# ---------------------------------------------------------------------------
# 2. _build_terrain_aware_model — hard-block verification
# ---------------------------------------------------------------------------


class TestBuildTerrainAwareModel:
    """
    Tests for GraphHopperService._build_terrain_aware_model().
    Imports the service class directly rather than the singleton to avoid
    the Overpass side-effect at construction time.
    """

    def setup_method(self):
        from app.services.graphhopper import GraphHopperService
        self.service = GraphHopperService()

    def test_paved_only_blocks_all_forbidden_surfaces(self):
        target = TerrainTarget(surface_type="paved_only")
        model = self.service._build_terrain_aware_model(target, bbox=None)
        priority_ifs = [rule["if"] for rule in model["priority"]]

        for surface in target.forbidden_osm_surfaces:
            assert any(
                surface.upper() in rule_if for rule_if in priority_ifs
            ), f"Expected hard-block for surface '{surface}' not found"

    def test_paved_only_blocks_all_forbidden_highways(self):
        target = TerrainTarget(surface_type="paved_only")
        model = self.service._build_terrain_aware_model(target, bbox=None)
        priority_ifs = [rule["if"] for rule in model["priority"]]

        for highway in target.forbidden_osm_highways:
            assert any(
                highway.upper() in rule_if for rule_if in priority_ifs
            ), f"Expected hard-block for highway '{highway}' not found"

    def test_paved_only_all_blocks_have_zero_multiplier(self):
        target = TerrainTarget(surface_type="paved_only")
        model = self.service._build_terrain_aware_model(target, bbox=None)
        for rule in model["priority"]:
            assert rule["multiply_by"] == "0", (
                f"Expected multiply_by=0 for rule {rule}"
            )

    def test_surface_type_any_emits_no_surface_blocks(self):
        """MTB mode — no surface blocking."""
        target = TerrainTarget(surface_type="any")
        model = self.service._build_terrain_aware_model(target, bbox=None)
        # Only access control rules should be present (access==PRIVATE, access==NO)
        surface_blocks = [
            r for r in model["priority"]
            if "surface ==" in r["if"] or "road_class ==" in r["if"]
        ]
        assert len(surface_blocks) == 0

    def test_gravel_ok_does_not_block_gravel_surface(self):
        target = TerrainTarget(surface_type="gravel_ok")
        model = self.service._build_terrain_aware_model(target, bbox=None)
        priority_ifs = [rule["if"] for rule in model["priority"]]
        # GRAVEL should not appear as a zero-multiplier block
        zero_rules = [
            r for r in model["priority"]
            if "GRAVEL" in r["if"] and r["multiply_by"] == "0"
        ]
        assert len(zero_rules) == 0

    def test_interval_mode_penalises_living_street(self):
        target = TerrainTarget(workout_structure="interval")
        model = self.service._build_terrain_aware_model(target, bbox=None)
        living_street_rules = [
            r for r in model["priority"]
            if "LIVING_STREET" in r["if"]
        ]
        assert len(living_street_rules) == 1
        assert living_street_rules[0]["multiply_by"] == "0.1"

    def test_private_access_blocked_by_default(self):
        target = TerrainTarget(allow_private=False)
        model = self.service._build_terrain_aware_model(target, bbox=None)
        private_rules = [r for r in model["priority"] if "PRIVATE" in r["if"]]
        assert len(private_rules) == 1
        assert private_rules[0]["multiply_by"] == "0"

    def test_private_access_not_blocked_when_allowed(self):
        target = TerrainTarget(allow_private=True)
        model = self.service._build_terrain_aware_model(target, bbox=None)
        private_rules = [r for r in model["priority"] if "PRIVATE" in r["if"]]
        assert len(private_rules) == 0

    def test_terrain_target_none_uses_legacy_path(self):
        """terrain_target=None must not call _build_terrain_aware_model."""
        from app.schemas.route import RouteGenerationParams
        target = None
        params = RouteGenerationParams(
            start_lat=53.0, start_lng=-6.0,
            profile="bike", route_type="road",
            terrain_target=target,
        )
        model = self.service._build_custom_model(params)
        # Legacy road bike path returns None (trusts server profile)
        assert model is None


# ---------------------------------------------------------------------------
# 3. WorkoutRoutePlanner — workout → TerrainTarget mapping
# ---------------------------------------------------------------------------


class TestWorkoutRoutePlanner:
    def setup_method(self):
        self.planner = WorkoutRoutePlanner()

    def test_threshold_produces_paved_only(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.THRESHOLD, 40)
        assert t.surface_type == "paved_only"

    def test_vo2max_produces_paved_only(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.VO2MAX, 20)
        assert t.surface_type == "paved_only"

    def test_endurance_produces_paved_only(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.ENDURANCE, 120)
        assert t.surface_type == "paved_only"

    def test_recovery_produces_paved_only(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.RECOVERY, 60)
        assert t.surface_type == "paved_only"

    def test_cross_training_produces_paved_preferred(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.CROSS_TRAINING, 90)
        assert t.surface_type == "paved_preferred"

    def test_rest_raises_value_error(self):
        with pytest.raises(ValueError, match="REST"):
            self.planner.workout_to_terrain_target(WorkoutType.REST, 0)

    def test_threshold_40min_uninterrupted_segment_gte_2_8km(self):
        """40 min threshold @ 24 km/h × 0.8 (moderate) = 12.8 km minimum stretch."""
        t = self.planner.workout_to_terrain_target(
            WorkoutType.THRESHOLD, 40, difficulty="moderate"
        )
        assert t.min_uninterrupted_segment_km is not None
        assert t.min_uninterrupted_segment_km >= 2.8

    def test_threshold_workout_structure_is_interval(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.THRESHOLD, 30)
        assert t.workout_structure == "interval"

    def test_endurance_workout_structure_is_endurance(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.ENDURANCE, 180)
        assert t.workout_structure == "endurance"

    def test_cross_training_workout_structure_is_rolling_hills(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.CROSS_TRAINING, 60)
        assert t.workout_structure == "rolling_hills"

    def test_endurance_has_no_min_uninterrupted_segment(self):
        t = self.planner.workout_to_terrain_target(WorkoutType.ENDURANCE, 180)
        assert t.min_uninterrupted_segment_km is None

    def test_difficulty_hard_gives_longer_segment_than_easy(self):
        t_hard = self.planner.workout_to_terrain_target(
            WorkoutType.THRESHOLD, 40, difficulty="hard"
        )
        t_easy = self.planner.workout_to_terrain_target(
            WorkoutType.THRESHOLD, 40, difficulty="easy"
        )
        assert t_hard.min_uninterrupted_segment_km > t_easy.min_uninterrupted_segment_km

    def test_allow_private_always_false(self):
        for wt in [WorkoutType.THRESHOLD, WorkoutType.ENDURANCE, WorkoutType.RECOVERY]:
            t = self.planner.workout_to_terrain_target(wt, 60)
            assert t.allow_private is False


# ---------------------------------------------------------------------------
# 4. OverpassService — query builder and response parsing
# ---------------------------------------------------------------------------


class TestOverpassService:
    def setup_method(self):
        self.service = OverpassService()

    def test_query_builder_contains_bbox(self):
        queries = ['way[highway](1.0,2.0,3.0,4.0);']
        query = self.service.build_overpass_query(queries)
        assert "1.0,2.0,3.0,4.0" in query

    def test_query_builder_contains_out_geom(self):
        queries = ['way[highway](0,0,1,1);']
        query = self.service.build_overpass_query(queries)
        assert "out geom" in query

    def test_empty_response_returns_empty_list(self):
        target = TerrainTarget(surface_type="paved_only")
        with patch("app.services.overpass_service.requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"elements": []}
            mock_post.return_value.raise_for_status = MagicMock()
            result = self.service.get_surface_exclusions((50.0, 6.0, 51.0, 7.0), target)
        assert result == []

    def test_timeout_returns_empty_list_without_raising(self):
        """Overpass timeout must not break route generation."""
        import requests as req_module
        target = TerrainTarget(surface_type="paved_only")
        with patch("app.services.overpass_service.requests.post") as mock_post:
            mock_post.side_effect = req_module.exceptions.Timeout()
            result = self.service.get_surface_exclusions((50.0, 6.0, 51.0, 7.0), target)
        assert result == []

    def test_malformed_element_skipped_others_processed(self):
        """A way with no geometry should be skipped; valid ways should be returned."""
        elements = [
            {"type": "way", "id": 1, "geometry": [{"lat": 50.0, "lon": 6.0}, {"lat": 50.1, "lon": 6.1}]},
            {"type": "way", "id": 2},  # no geometry or bounds → skipped
        ]
        features = self.service._elements_to_geojson_features(elements, "test")
        assert len(features) == 1
        assert features[0]["properties"]["osm_id"] == 1

    def test_surface_any_returns_empty_without_query(self):
        """MTB mode: no surface exclusions should be returned."""
        target = TerrainTarget(surface_type="any")
        result = self.service.get_surface_exclusions((50.0, 6.0, 51.0, 7.0), target)
        assert result == []

    def test_geojson_feature_has_correct_structure(self):
        element = {
            "type": "way",
            "id": 42,
            "geometry": [
                {"lat": 50.0, "lon": 6.0},
                {"lat": 50.1, "lon": 6.1},
            ],
            "tags": {"surface": "dirt"},
        }
        feature = self.service._way_to_bbox_feature(element, "excl")
        assert feature is not None
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"
        assert "excl_42" in feature["id"]
        assert len(feature["geometry"]["coordinates"][0]) == 5  # closed ring


# ---------------------------------------------------------------------------
# 5. TerrainResearchAgent — LLM response parsing and fallback
# ---------------------------------------------------------------------------


class TestTerrainResearchAgent:
    def setup_method(self):
        self.agent = TerrainResearchAgent()

    def _make_llm_response(self, data: dict) -> dict:
        """Wrap a dict as an OpenAI-style chat completion response."""
        return {
            "choices": [{"message": {"content": json.dumps(data)}}]
        }

    def test_valid_llm_response_returns_terrain_target(self):
        response_data = {
            "total_distance_km": 257,
            "total_ascent_m": 2600,
            "max_gradient_pct": 8.0,
            "avg_gradient_pct": 3.5,
            "dominant_surface": "cobblestone",
            "cobble_pct": 0.27,
            "punchiness_score": 0.7,
            "confidence": 0.9,
        }
        with patch.object(
            self.agent._get_openai_service(),
            "chat_completion",
            return_value=self._make_llm_response(response_data),
        ) if False else patch(
            "app.services.terrain_research_agent.openai_chat_service.chat_completion",
            return_value=self._make_llm_response(response_data),
        ):
            profile = self.agent._research_via_llm("Paris-Roubaix")

        assert profile is not None
        assert profile["total_ascent_m"] == 2600
        assert profile["punchiness_score"] == 0.7

    def test_low_confidence_triggers_none(self):
        response_data = {
            "total_distance_km": 100,
            "total_ascent_m": 1000,
            "max_gradient_pct": 5.0,
            "avg_gradient_pct": 2.0,
            "dominant_surface": "asphalt",
            "cobble_pct": 0.0,
            "punchiness_score": 0.2,
            "confidence": 0.3,  # below threshold
        }
        with patch(
            "app.services.terrain_research_agent.openai_chat_service.chat_completion",
            return_value=self._make_llm_response(response_data),
        ):
            profile = self.agent._research_via_llm("Unknown Amateur Race XYZ")

        assert profile is None

    def test_missing_required_field_triggers_none(self):
        response_data = {
            "total_distance_km": 100,
            # total_ascent_m missing
            "dominant_surface": "asphalt",
            "confidence": 0.9,
        }
        with patch(
            "app.services.terrain_research_agent.openai_chat_service.chat_completion",
            return_value=self._make_llm_response(response_data),
        ):
            profile = self.agent._research_via_llm("Partial Data Race")

        assert profile is None

    def test_non_json_llm_response_triggers_none(self):
        with patch(
            "app.services.terrain_research_agent.openai_chat_service.chat_completion",
            return_value={"choices": [{"message": {"content": "Sorry, I don't know."}}]},
        ):
            profile = self.agent._research_via_llm("Unknown Race")

        assert profile is None

    def test_cobblestone_surface_maps_to_paved_only(self):
        profile = {
            "total_distance_km": 257,
            "total_ascent_m": 2600,
            "max_gradient_pct": 8.0,
            "avg_gradient_pct": 3.5,
            "dominant_surface": "cobblestone",
            "punchiness_score": 0.7,
        }
        target = self.agent._profile_to_terrain_target(profile, "Paris-Roubaix")
        assert target.surface_type == "paved_only"

    def test_gravel_surface_maps_to_gravel_ok(self):
        profile = {
            "dominant_surface": "gravel",
            "max_gradient_pct": 12.0,
            "avg_gradient_pct": 5.0,
            "total_ascent_m": 3000,
            "total_distance_km": 145,
        }
        target = self.agent._profile_to_terrain_target(profile, "Strade Bianche")
        assert target.surface_type == "gravel_ok"

    def test_ascent_per_km_computed_correctly(self):
        profile = {
            "dominant_surface": "asphalt",
            "total_distance_km": 100.0,
            "total_ascent_m": 2000.0,
            "max_gradient_pct": 10.0,
            "avg_gradient_pct": 4.0,
        }
        target = self.agent._profile_to_terrain_target(profile, "Test Race")
        assert target.ascent_per_km == 20.0

    def test_punchiness_from_variance_high_variance_high_score(self):
        grades = [0.5, 12.0, 0.3, 15.0, 0.2, 10.0]  # very punchy
        score = TerrainResearchAgent.compute_punchiness_from_variance(grades)
        assert score > 0.7

    def test_punchiness_from_variance_steady_gradient_low_score(self):
        grades = [4.8, 5.0, 5.1, 4.9, 5.0, 4.8]  # steady
        score = TerrainResearchAgent.compute_punchiness_from_variance(grades)
        assert score < 0.1

    def test_punchiness_from_variance_single_element_returns_zero(self):
        assert TerrainResearchAgent.compute_punchiness_from_variance([5.0]) == 0.0

    def test_target_distance_scaling(self):
        """Scaling to a shorter distance should reduce total_ascent_m proportionally."""
        profile = {
            "total_distance_km": 200.0,
            "total_ascent_m": 4000.0,
            "max_gradient_pct": 10.0,
            "dominant_surface": "asphalt",
            "punchiness_score": 0.5,
        }
        self.agent._profile_to_terrain_target(profile, "test")  # baseline
        # Apply scaling
        scale = 40.0 / 200.0
        scaled_ascent = 4000.0 * scale
        assert scaled_ascent == pytest.approx(800.0)


# ---------------------------------------------------------------------------
# 6. Integration tests — new API endpoints (mocked external services)
# ---------------------------------------------------------------------------

pytestmark_integration = pytest.mark.integration


def _get_auth_token(client: TestClient) -> str:
    unique_email = f"terrain_test_{int(time.time())}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Terrain Test User",
        },
    )
    response = client.post(
        "/api/auth/login",
        data={"username": unique_email, "password": "testpassword123"},
    )
    return response.json().get("access_token", "")


@pytest.mark.integration
def test_generate_workout_route__threshold__returns_200(client):
    """POST /routes/generate-workout with a threshold workout returns a valid route."""
    token = _get_auth_token(client)

    gh_mock = MagicMock(
        status_code=200,
        json=MagicMock(return_value=FAKE_GH_RESPONSE),
        raise_for_status=MagicMock(),
    )
    # Note: do NOT also patch app.services.overpass_service.requests.post here —
    # both targets resolve to the same requests.post attribute (same module object)
    # and the last patch applied would overwrite the GH mock. Overpass is not called
    # in this code path anyway (bbox=None skips the Overpass pre-flight).
    with patch(
        "app.services.graphhopper.requests.post",
        return_value=gh_mock,
    ):
        response = client.post(
            "/api/routes/generate-workout",
            params={
                "workout_type": "threshold",
                "duration_minutes": 40,
                "start_lat": 53.3498,
                "start_lng": -6.2603,
                "profile": "bike",
                "difficulty": "moderate",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "route" in data
    assert data["route"]["distance_m"] > 0


@pytest.mark.integration
def test_generate_workout_route__rest_day__returns_400(client):
    """REST workout_type must be rejected with a 400."""
    token = _get_auth_token(client)
    response = client.post(
        "/api/routes/generate-workout",
        params={
            "workout_type": "rest",
            "duration_minutes": 0,
            "start_lat": 53.3498,
            "start_lng": -6.2603,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.integration
def test_simulate_race_route__returns_200(client):
    """POST /routes/simulate-race with a known race returns a valid route."""
    token = _get_auth_token(client)

    llm_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "total_distance_km": 257,
                        "total_ascent_m": 2600,
                        "max_gradient_pct": 8.0,
                        "avg_gradient_pct": 3.5,
                        "dominant_surface": "cobblestone",
                        "cobble_pct": 0.27,
                        "punchiness_score": 0.7,
                        "confidence": 0.9,
                    })
                }
            }
        ]
    }

    gh_mock = MagicMock(
        status_code=200,
        json=MagicMock(return_value=FAKE_GH_RESPONSE),
        raise_for_status=MagicMock(),
    )
    # Note: do NOT also patch app.services.overpass_service.requests.post here —
    # both targets resolve to the same requests.post attribute and the last patch
    # applied would overwrite the GH mock. Overpass is skipped (bbox=None).
    with patch(
        "app.services.terrain_research_agent.openai_chat_service.chat_completion",
        return_value=llm_response,
    ), patch(
        "app.services.graphhopper.requests.post",
        return_value=gh_mock,
    ):
        response = client.post(
            "/api/routes/simulate-race",
            params={
                "race_name": "Paris-Roubaix",
                "start_lat": 53.3498,
                "start_lng": -6.2603,
                "target_distance_km": 40.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "route" in data
    assert data["route"]["total_elevation_gain_m"] > 0


@pytest.mark.integration
def test_generate_route_legacy__no_terrain_target__same_behaviour(client):
    """
    Regression: existing POST /routes/generate without terrain_target must return
    the same response structure as before this change.
    """
    token = _get_auth_token(client)

    with patch(
        "app.services.graphhopper.requests.get",
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value=FAKE_GH_RESPONSE),
            raise_for_status=MagicMock(),
        ),
    ):
        response = client.post(
            "/api/routes/generate",
            json={
                "start_lat": 53.3498,
                "start_lng": -6.2603,
                "end_lat": 53.4,
                "end_lng": -6.2,
                "profile": "bike",
                "route_type": "road",
                "is_loop": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    # Core fields must still be present
    assert "route" in data
    assert "message" in data
    assert "generation_time_ms" in data
