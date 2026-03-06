"""
Race terrain research agent for Race Simulation routing mode.

Given a race name, this agent:
  1. Asks OpenAI to return structured terrain data about the race
     (total distance, ascent, gradient, surface, confidence score).
  2. If the LLM confidence is below threshold or parsing fails,
     falls back to Strava's segment explorer in the user's local area
     to derive gradient statistics from real segment data.
  3. Returns a TerrainTarget that can be fed into RouteGenerationParams
     to generate a local route that mimics the race's terrain profile.

The OpenAI call uses json_object response format so the output is always
machine-readable. If the model cannot find reliable data for a race it
should return confidence < 0.5 which triggers the Strava fallback.
"""
import json
import logging
import math
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.user import Profile
from app.schemas.terrain import TerrainTarget
from app.services.openai_chat import openai_chat_service
from app.services.strava_route_integration import strava_route_integration

logger = logging.getLogger(__name__)

# Minimum confidence score from the LLM response before triggering Strava fallback
_MIN_LLM_CONFIDENCE = 0.5

# Required fields in the LLM JSON response
_REQUIRED_LLM_FIELDS = {
    "total_distance_km",
    "total_ascent_m",
    "max_gradient_pct",
    "dominant_surface",
    "confidence",
}

_SYSTEM_PROMPT = """You are a professional cycling race analyst with comprehensive knowledge
of professional cycling races worldwide.

When asked about a race, return a JSON object with EXACTLY these fields:
{
  "total_distance_km": <number, total race distance in km>,
  "total_ascent_m": <number, total elevation gain in metres>,
  "max_gradient_pct": <number, steepest gradient in percent>,
  "avg_gradient_pct": <number, average gradient of climbs>,
  "dominant_surface": <string, one of: "asphalt", "cobblestone", "gravel", "mixed">,
  "cobble_pct": <number 0-1, fraction of route on cobblestones>,
  "punchiness_score": <number 0-1, 0=steady gradient, 1=many short steep punchy climbs>,
  "confidence": <number 0-1, your confidence in the accuracy of this data>
}

If you are not confident about the race data, set confidence below 0.5.
Return ONLY the JSON object, no additional text."""


class TerrainResearchAgent:
    """
    LLM-assisted race terrain research service.

    Falls back to Strava segment analysis when LLM confidence is insufficient.
    """

    def research_race(
        self,
        race_name: str,
        user_lat: float,
        user_lng: float,
        db: Session,
        user_id: Optional[str] = None,
        target_distance_km: Optional[float] = None,
    ) -> TerrainTarget:
        """
        Research a race and return a TerrainTarget representing its terrain profile.

        target_distance_km: if set, scale the race profile to a shorter/longer local route
          (keeps ascent_per_km ratio, adjusts total_ascent_m proportionally).
        """
        logger.info(f"Researching race terrain: '{race_name}'")

        # --- Primary path: LLM race research ---
        profile = self._research_via_llm(race_name)

        if profile is None:
            logger.info(f"LLM research failed for '{race_name}', falling back to Strava")
            profile = self._research_via_strava(user_lat, user_lng, db, user_id)

        if profile is None:
            logger.warning(
                f"Both LLM and Strava fallback failed for '{race_name}'. "
                "Using conservative paved-road defaults."
            )
            profile = self._default_profile()

        # --- Scale to target distance if requested ---
        if target_distance_km and profile.get("total_distance_km"):
            scale = target_distance_km / profile["total_distance_km"]
            profile["total_ascent_m"] = round(
                profile.get("total_ascent_m", 0) * scale, 0
            )
            profile["total_distance_km"] = target_distance_km

        return self._profile_to_terrain_target(profile, race_name)

    # ── LLM research ─────────────────────────────────────────────────────────

    def _research_via_llm(
        self, race_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Call OpenAI to get race terrain data.
        Returns parsed profile dict or None on failure / low confidence.
        """
        try:
            response = openai_chat_service.chat_completion(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Describe the terrain profile of: {race_name}",
                    },
                ],
                model="gpt-4o",
                max_tokens=500,
                temperature=0.1,  # Low temperature for factual recall
                response_format={"type": "json_object"},
            )

            # Extract text content from OpenAI response
            raw_content = self._extract_response_content(response)
            if not raw_content:
                logger.warning("LLM returned empty content for race research")
                return None

            profile = json.loads(raw_content)

            # Validate required fields
            missing = _REQUIRED_LLM_FIELDS - set(profile.keys())
            if missing:
                logger.warning(
                    f"LLM response missing required fields: {missing}. "
                    "Triggering fallback."
                )
                return None

            confidence = float(profile.get("confidence", 0))
            if confidence < _MIN_LLM_CONFIDENCE:
                logger.info(
                    f"LLM confidence {confidence:.2f} below threshold {_MIN_LLM_CONFIDENCE} "
                    f"for '{race_name}' — triggering Strava fallback"
                )
                return None

            logger.info(
                f"LLM research successful for '{race_name}': "
                f"dist={profile.get('total_distance_km')}km, "
                f"ascent={profile.get('total_ascent_m')}m, "
                f"confidence={confidence:.2f}"
            )
            return profile

        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned non-JSON response: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM race research failed: {e}")
            return None

    def _extract_response_content(self, response: Any) -> Optional[str]:
        """Extract string content from various OpenAI response formats."""
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            # Standard OpenAI chat completion format
            choices = response.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        # Handle openai SDK response objects
        try:
            return response.choices[0].message.content
        except (AttributeError, IndexError):
            pass
        return None

    # ── Strava fallback ───────────────────────────────────────────────────────

    def _research_via_strava(
        self,
        lat: float,
        lng: float,
        db: Session,
        user_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Derive a terrain profile from Strava segments near the user's location.
        Returns a partial profile (no total_distance_km) with gradient statistics.
        """
        if user_id is None:
            logger.info("No user_id provided — cannot perform Strava segment fallback")
            return None

        try:
            segments = strava_route_integration.get_user_popular_segments(
                user_id=user_id, db=db, lat=lat, lng=lng, radius_km=50
            )
        except Exception as e:
            logger.warning(f"Strava segment fetch failed: {e}")
            return None

        if not segments:
            return None

        # Extract gradient data from segments
        grades = [
            s["average_grade"]
            for s in segments
            if s.get("average_grade") is not None
        ]
        elevation_gains = [
            s["elevation_high"] - s["elevation_low"]
            for s in segments
            if s.get("elevation_high") is not None and s.get("elevation_low") is not None
        ]

        if not grades:
            return None

        avg_grade = sum(grades) / len(grades)
        max_grade = max(grades)

        # Punchiness: fraction of segments with grade > 5%
        punchy_count = sum(1 for g in grades if g > 5.0)
        punchiness = round(punchy_count / len(grades), 2)

        total_elevation = sum(elevation_gains) if elevation_gains else 0

        logger.info(
            f"Strava fallback: {len(segments)} segments, "
            f"avg_grade={avg_grade:.1f}%, max_grade={max_grade:.1f}%, "
            f"punchiness={punchiness}"
        )

        return {
            "total_distance_km": None,  # Unknown from segment data
            "total_ascent_m": total_elevation,
            "max_gradient_pct": max_grade,
            "avg_gradient_pct": avg_grade,
            "dominant_surface": "asphalt",
            "cobble_pct": 0.0,
            "punchiness_score": punchiness,
            "confidence": 0.6,  # Moderate confidence from local segment data
        }

    # ── Profile → TerrainTarget conversion ───────────────────────────────────

    def _profile_to_terrain_target(
        self, profile: Dict[str, Any], race_name: str
    ) -> TerrainTarget:
        """
        Convert a terrain profile dict to a TerrainTarget.

        Surface mapping:
          asphalt → paved_only
          cobblestone → paved_only  (cobbles are technically paved)
          gravel → gravel_ok
          mixed → paved_preferred
        """
        dominant_surface = profile.get("dominant_surface", "asphalt").lower()
        surface_type_map = {
            "asphalt": "paved_only",
            "cobblestone": "paved_only",
            "gravel": "gravel_ok",
            "mixed": "paved_preferred",
        }
        surface_type = surface_type_map.get(dominant_surface, "paved_only")

        max_gradient = profile.get("max_gradient_pct")
        avg_gradient = profile.get("avg_gradient_pct")

        # Derive grade_range from avg gradient (±30% of average, floored at 0)
        grade_range = None
        if avg_gradient is not None and avg_gradient > 0:
            grade_min = max(0.0, round(avg_gradient * 0.7, 1))
            grade_max = round(avg_gradient * 1.3, 1)
            grade_range = (grade_min, grade_max)

        # ascent_per_km — only if we have both total_ascent and total_distance
        ascent_per_km = None
        total_distance = profile.get("total_distance_km")
        total_ascent = profile.get("total_ascent_m")
        if total_distance and total_ascent and total_distance > 0:
            ascent_per_km = round(total_ascent / total_distance, 1)

        return TerrainTarget(
            surface_type=surface_type,
            allow_private=False,
            allow_no_exit=False,
            ascent_per_km=ascent_per_km,
            total_ascent_m=total_ascent,
            max_gradient_pct=max_gradient,
            punchiness_score=profile.get("punchiness_score"),
            workout_structure="race_simulation",
            grade_range=grade_range,
            race_name=race_name,
        )

    def _default_profile(self) -> Dict[str, Any]:
        """Conservative default when all research paths fail."""
        return {
            "total_distance_km": None,
            "total_ascent_m": 500,
            "max_gradient_pct": 8.0,
            "avg_gradient_pct": 3.0,
            "dominant_surface": "asphalt",
            "cobble_pct": 0.0,
            "punchiness_score": 0.3,
            "confidence": 0.3,
        }

    @staticmethod
    def compute_punchiness_from_variance(grades: List[float]) -> float:
        """
        Compute punchiness score from gradient variance.
        High variance (many short steep efforts) → score close to 1.
        Exposed as a static method for testability.
        """
        if len(grades) < 2:
            return 0.0
        mean = sum(grades) / len(grades)
        variance = sum((g - mean) ** 2 for g in grades) / len(grades)
        std_dev = math.sqrt(variance)
        # Normalise: std_dev of 5% → punchiness ≈ 1.0
        return round(min(std_dev / 5.0, 1.0), 2)


# Service instance
terrain_research_agent = TerrainResearchAgent()
